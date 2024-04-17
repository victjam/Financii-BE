from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from controller.auth import get_current_user
from models.account import Account
from models.user import UserInDB
from db.client import db_client
from db.schemas.account import account_schema
from bson import ObjectId
from datetime import datetime, timedelta

router = APIRouter(prefix="/accounts", tags=["Accounts"])


def parse_datetime(date_str: str) -> datetime:
    """Parse the incoming date string to datetime, assuming UTC."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


@router.post("/", response_model=Account)
async def create_account(account: Account, current_user: UserInDB = Depends(get_current_user)):
    account_dict = account.dict(exclude_unset=True)
    account_dict["user_id"] = current_user.id
    account_dict["createdAt"] = datetime.now()
    account_dict["updatedAt"] = None

    result = db_client.accounts.insert_one(account_dict)
    new_account = db_client.accounts.find_one({"_id": result.inserted_id})
    return account_schema(new_account)


@router.get("/", response_model=List[Account])
async def get_accounts_with_filtered_balances(
    current_user: UserInDB = Depends(get_current_user),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
):
    try:
        query = {"user_id": current_user.id}
        if startDate and endDate:
            start_datetime = parse_datetime(startDate)
            end_datetime = parse_datetime(endDate)
            end_datetime += timedelta(seconds=1)
            query["createdAt"] = {"$gte": start_datetime, "$lt": end_datetime}

        accounts = db_client.accounts.find(query)
        results = []
        for account in accounts:
            # Initialize balance from the stored initial balance
            balance = account.get("balance", 0.0)
            if startDate and endDate:
                # Adjust the query to filter transactions within the date range
                transactions = db_client.transactions.aggregate([
                    {"$match": {
                        "account_id": ObjectId(account["_id"]),
                        "createdAt": {"$gte": start_datetime, "$lte": end_datetime}
                    }},
                    {"$group": {
                        "_id": "$account_id",
                        "total": {"$sum": "$amount"}
                    }}
                ])
                transaction_total = list(transactions)
                if transaction_total:
                    balance += transaction_total[0]['total']

            account_data = account_schema(account)
            account_data['balance'] = balance
            results.append(account_data)

        return results
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Ha ocurrido un error: " + str(e))


@router.put("/{account_id}", response_model=Account)
async def update_account(account_id: str, account: Account, current_user: UserInDB = Depends(get_current_user)):
    existing_account = db_client.accounts.find_one(
        {"_id": ObjectId(account_id), "user_id": current_user.id})
    if not existing_account:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    update_data = account.model_dump(
        exclude_unset=True, exclude={"createdAt", "id"})
    update_data['updatedAt'] = datetime.now()

    db_client.accounts.update_one(
        {"_id": ObjectId(account_id), "user_id": current_user.id},
        {"$set": update_data}
    )

    updated_account = db_client.accounts.find_one(
        {"_id": ObjectId(account_id)})
    if not updated_account:
        raise HTTPException(
            status_code=404, detail="La cuenta que se quiere actualizar no existe")

    return account_schema(updated_account)


@router.delete("/{account_id}", tags=["Accounts"])
async def delete_account(account_id: str, current_user: UserInDB = Depends(get_current_user)):
    # Convert the account_id to ObjectId to ensure compatibility with MongoDB
    try:
        account_object_id = ObjectId(account_id)
    except Exception:
        raise HTTPException(
            status_code=400, detail="Invalid account ID format")
    print("account_object_id: ", account_object_id)

    # First, delete all transactions associated with this account
    transactions_deletion_result = db_client.transactions.delete_many(
        {"account_id": account_id})

    # Then, delete the account itself
    account_deletion_result = db_client.accounts.delete_one(
        {"_id": account_object_id, "user_id": current_user.id})

    if account_deletion_result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Cuenta no encontrada")

    return {
        "message": "La cuenta y sus transacciones han sido eliminadas",
        "transactions_deleted": transactions_deletion_result.deleted_count
    }
