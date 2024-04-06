from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from controller.auth import get_current_user
from models.transaction import Transaction
from db.client import db_client
from db.schemas.transaction import transaction_schema
from bson import ObjectId

from models.user import UserInDB

router = APIRouter(prefix="/transactions", tags=["Transactions"])


def update_account_balance(account_id: ObjectId, amount, transaction_type: str):
    try:
        amount = float(amount)
    except ValueError:
        raise ValueError("Amount must be a number")

    if transaction_type == "income":
        new_balance = {"$inc": {"balance": amount}}
    elif transaction_type == "expense":
        new_balance = {"$inc": {"balance": -amount}}
    db_client.accounts.update_one({"_id": account_id}, new_balance)


@router.post("/", tags=["Transactions"])
async def create_transaction(transaction: Transaction, current_user: UserInDB = Depends(get_current_user)):
    transaction_dict = dict(transaction)
    transaction_dict["user_id"] = current_user.id

    try:
        transaction_dict["amount"] = float(transaction_dict["amount"])
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid amount format")

    if transaction_dict["type"] not in ["income", "expense"]:
        raise HTTPException(
            status_code=400, detail="Transaction type must be either 'income' or 'expense'")

    result = db_client.transactions.insert_one(transaction_dict)
    new_transaction = db_client.transactions.find_one(
        {"_id": result.inserted_id})

    update_account_balance(ObjectId(
        transaction_dict["account_id"]), transaction_dict["amount"], transaction_dict["type"])

    return transaction_schema(new_transaction)


@router.get("/", tags=["Transactions"])
async def get_transactions(current_user: UserInDB = Depends(get_current_user)):
    transactions = db_client.transactions.find({"user_id": current_user.id})
    return [Transaction(**transaction_schema(transaction)) for transaction in transactions]


@router.get("/{transaction_id}", tags=["Transactions"])
async def get_transaction(transaction_id: str, current_user: UserInDB = Depends(get_current_user)):
    transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id)})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")
    return Transaction(**transaction_schema(transaction))


@router.put("/{transaction_id}", tags=["Transactions"])
async def update_transaction(transaction_id: str, transaction_data: Transaction, current_user: UserInDB = Depends(get_current_user)):
    existing_transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": current_user.id})
    if not existing_transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    transaction_dict = dict(transaction_data)
    new_account_id = transaction_dict.get(
        "account_id", existing_transaction["account_id"])
    old_account_id = existing_transaction["account_id"]

    old_amount = float(existing_transaction["amount"])
    new_amount = float(transaction_dict.get("amount", old_amount))
    amount_adjustment = new_amount - old_amount

    if new_account_id != old_account_id:
        revert_adjustment = - \
            old_amount if existing_transaction["type"] == "income" else old_amount
        db_client.accounts.update_one(
            {"_id": ObjectId(old_account_id)},
            {"$inc": {"balance": revert_adjustment}}
        )

        apply_adjustment = new_amount if existing_transaction["type"] == "income" else -new_amount
        db_client.accounts.update_one(
            {"_id": ObjectId(new_account_id)},
            {"$inc": {"balance": apply_adjustment}}
        )

    db_client.transactions.update_one(
        {"_id": ObjectId(transaction_id)},
        {"$set": transaction_dict}
    )

    if new_account_id == old_account_id and amount_adjustment != 0:
        balance_adjustment = amount_adjustment if existing_transaction[
            "type"] == "income" else -amount_adjustment
        db_client.accounts.update_one(
            {"_id": ObjectId(old_account_id)},
            {"$inc": {"balance": balance_adjustment}}
        )

    updated_transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id)})
    return transaction_schema(updated_transaction)


@router.delete("/{transaction_id}", tags=["Transactions"])
async def delete_transaction(transaction_id: str, current_user: UserInDB = Depends(get_current_user)):
    transaction = db_client.transactions.find_one(
        {"_id": ObjectId(transaction_id), "user_id": current_user.id})
    if not transaction:
        raise HTTPException(status_code=404, detail="Transaction not found")

    adjustment = transaction["amount"] if transaction["type"] == "income" else - \
        transaction["amount"]

    db_client.accounts.update_one(
        {"_id": ObjectId(transaction["account_id"])},
        {"$inc": {"balance": -adjustment}}
    )

    db_client.transactions.delete_one({"_id": ObjectId(transaction_id)})

    return {"message": "Transaction deleted and account balance updated"}
