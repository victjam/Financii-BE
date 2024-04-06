from typing import List
from fastapi import APIRouter, Depends, HTTPException
from controller.auth import get_current_user
from models.account import Account
from models.user import UserInDB
from db.client import db_client
from db.schemas.account import account_schema
from bson import ObjectId
from datetime import datetime

router = APIRouter(prefix="/accounts", tags=["Accounts"])


@router.post("/", response_model=Account)
async def create_account(account: Account, current_user: UserInDB = Depends(get_current_user)):
    account_dict = dict(account)
    account_dict["user_id"] = current_user.id
    result = db_client.accounts.insert_one(account_dict)
    new_account = db_client.accounts.find_one({"_id": result.inserted_id})
    return account_schema(new_account)


@router.get("/", response_model=List[dict])
async def get_accounts_with_balances(current_user: UserInDB = Depends(get_current_user)):
    account_documents = db_client.accounts.find({"user_id": current_user.id})
    return [account_schema(account) for account in account_documents]


@router.put("/{account_id}", response_model=Account)
async def update_account(account_id: str, account: Account, current_user: UserInDB = Depends(get_current_user)):
    account_dict = dict(account)
    db_client.accounts.update_one(
        {"_id": ObjectId(account_id)}, {"$set": account_dict})
    updated_account = db_client.accounts.find_one(
        {"_id": ObjectId(account_id)})
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
        raise HTTPException(status_code=404, detail="Account not found")

    return {
        "message": "Account and all associated transactions deleted",
        "transactions_deleted": transactions_deletion_result.deleted_count
    }
