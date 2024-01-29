from fastapi import APIRouter, Depends, HTTPException
from controller.auth import get_current_user
from models.transaction import Transaction
from db.client import db_client
from db.schemas.transaction import transaction_schema
from bson import ObjectId

from models.user import UserInDB

router = APIRouter(prefix="/transactions", tags=["Transactions"])


@router.get("/total", tags=["Transactions"])
async def get_total_transactions(current_user: UserInDB = Depends(get_current_user)):
    transactions = db_client.transactions.find({"user_id": current_user.id})
    total_amount = 0
    for transaction in transactions:
        amount = transaction.get('amount', 0)
        if isinstance(amount, str):
            amount = float(amount.replace(',', ''))
        total_amount += amount
    formatted_total = "{:.2f}".format(round(total_amount, 2))
    return {"total": formatted_total}


@router.post("/", tags=["Transactions"])
async def create_transaction(transaction: Transaction, current_user: UserInDB = Depends(get_current_user)):
    transaction_dict = dict(transaction)
    del transaction_dict["id"]
    id = db_client.transactions.insert_one(transaction_dict).inserted_id
    new_transaction = transaction_schema(
        db_client.transactions.find_one({"_id": id}))
    return Transaction(**new_transaction)


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
async def update_transaction(transaction_id: str, transaction: Transaction, current_user: UserInDB = Depends(get_current_user)):
    transaction_dict = dict(transaction)
    del transaction_dict["id"]
    db_client.transactions.update_one({"_id": ObjectId(transaction_id)}, {
                                      "$set": transaction_dict})
    updated_transaction = transaction_schema(
        db_client.transactions.find_one({"_id": ObjectId(transaction_id)}))
    return Transaction(**updated_transaction)
