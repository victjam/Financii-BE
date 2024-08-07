from datetime import datetime, timedelta
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from controller.auth import get_current_user
from models.transaction import Transaction
from db.client import db_client
from db.schemas.transaction import transaction_schema
from bson import ObjectId

from models.user import UserInDB

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def parse_datetime(date_str: str) -> datetime:
    """Parse the incoming date string to datetime, assuming UTC."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


def update_account_balance(account_id, amount, transaction_type):
    try:
        account = db_client.accounts.find_one({"_id": ObjectId(account_id)})
        if not account:
            raise HTTPException(status_code=404, detail="Cuenta no encontrada")

        amount = float(amount)
        if transaction_type == "expense":
            amount = -amount  # Subtract for expenses

        new_balance = account['balance'] + amount
        db_client.accounts.update_one(
            {"_id": ObjectId(account_id)},
            {"$set": {"balance": new_balance}}
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/", tags=["Transactions"])
async def create_transaction(transaction: Transaction, current_user: UserInDB = Depends(get_current_user)):
    transaction_dict = dict(transaction)
    transaction_dict["user_id"] = current_user.id
    transaction_dict["updatedAt"] = None

    try:
        transaction_dict["amount"] = float(transaction_dict["amount"])
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Formato de monto invalido")

    if transaction_dict["type"] not in ["income", "expense"]:
        raise HTTPException(
            status_code=400, detail="La transacción debe ser de tipo ingreso o egreso")

    result = db_client.transactions.insert_one(transaction_dict)
    new_transaction = db_client.transactions.find_one(
        {"_id": result.inserted_id})

    update_account_balance(
        transaction_dict["account_id"], transaction_dict["amount"], transaction_dict["type"])

    return transaction_schema(new_transaction)


@router.get("/", response_model=List[Transaction])
async def get_transactions(
    current_user: UserInDB = Depends(get_current_user),
    startDate: Optional[str] = Query(None),
    endDate: Optional[str] = Query(None)
):
    if startDate and endDate:
        start_datetime = parse_datetime(startDate)
        end_datetime = parse_datetime(endDate)

        # Expand end_datetime by one second to ensure inclusion of transactions at the exact end time
        end_datetime += timedelta(seconds=1)

        query = {
            "user_id": current_user.id,
            "createdAt": {"$gte": start_datetime, "$lt": end_datetime}
        }
        transactions = db_client.transactions.find(query).sort("createdAt", 1)
        return [Transaction(**transaction_schema(transaction)) for transaction in transactions]
    else:
        transactions = db_client.transactions.find(
            {"user_id": current_user.id}).sort("createdAt", 1)
        return [Transaction(**transaction_schema(transaction)) for transaction in transactions]


@router.get("/{transaction_id}", tags=["Transactions"])
async def get_transaction(transaction_id: str, current_user: UserInDB = Depends(get_current_user)):
    transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id)})
    if not transaction:
        raise HTTPException(status_code=404, detail="La transacción no existe")
    return Transaction(**transaction_schema(transaction))


@router.put("/{transaction_id}", tags=["Transactions"])
async def update_transaction(transaction_id: str, transaction_data: Transaction, current_user: UserInDB = Depends(get_current_user)):
    existing_transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": current_user.id})
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="La transacción no existe")

    transaction_dict = transaction_data.dict()
    transaction_dict["updatedAt"] = datetime.now()
    transaction_dict["user_id"] = current_user.id

    new_account_id = transaction_dict.get(
        "account_id", existing_transaction["account_id"])
    old_account_id = existing_transaction["account_id"]

    old_amount = float(existing_transaction["amount"])
    new_amount = float(transaction_dict.get("amount", old_amount))
    old_type = existing_transaction["type"]
    new_type = transaction_dict["type"]

    if old_type == "income":
        revert_adjustment = -old_amount
    else:
        revert_adjustment = old_amount
    db_client.accounts.update_one(
        {"_id": ObjectId(old_account_id)},
        {"$inc": {"balance": revert_adjustment}}
    )

    if new_type == "income":
        apply_adjustment = new_amount
    else:
        apply_adjustment = -new_amount
    db_client.accounts.update_one(
        {"_id": ObjectId(new_account_id)},
        {"$inc": {"balance": apply_adjustment}}
    )

    # Update the transaction
    db_client.transactions.update_one(
        {"_id": ObjectId(transaction_id)},
        {"$set": transaction_dict}
    )

    updated_transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id)})
    return transaction_schema(updated_transaction)


@router.delete("/{transaction_id}", tags=["Transactions"])
async def delete_transaction(transaction_id: str, current_user: UserInDB = Depends(get_current_user)):
    transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": current_user.id})
    if not transaction:
        raise HTTPException(status_code=404, detail="La transacción no existe")

    try:
        amount = float(transaction["amount"])
        adjustment = amount if transaction["type"] == "income" else -amount
    except ValueError as e:
        raise HTTPException(
            status_code=400, detail=f"Formato de balance invalido: {transaction['amount']}")

    db_client.accounts.update_one(
        {"_id": ObjectId(transaction["account_id"])},
        {"$inc": {"balance": -adjustment}}
    )

    db_client.transactions.delete_one({"_id": ObjectId(transaction_id)})

    return {"message": "Transacción eliminada y balance actualizado"}
