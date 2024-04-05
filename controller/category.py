from fastapi import APIRouter, Depends, HTTPException
from typing import List
from models.category import Category
from controller.auth import get_current_user
from db.client import db_client
from db.schemas.category import category_schema
from bson import ObjectId
from datetime import datetime

from models.user import UserInDB

router = APIRouter(prefix="/categories", tags=["Categories"])


@router.post("/", response_model=Category)
async def create_category(category: Category, current_user: UserInDB = Depends(get_current_user)):
    category_dict = dict(category)
    category_dict["user_id"] = current_user.id
    category_dict["date"] = datetime.now()
    result = db_client.categories.insert_one(category_dict)
    new_category = db_client.categories.find_one({"_id": result.inserted_id})
    return category_schema(new_category)


@router.get("/", tags=["Categories"])
async def get_categories(current_user: UserInDB = Depends(get_current_user)):
    categories = db_client.categories.find({"user_id": current_user.id})
    return [Category(**category_schema(category)) for category in categories]


@router.put("/{category_id}", tags=["Transactions"])
async def update_category(category_id: str, category: Category, current_user: UserInDB = Depends(get_current_user)):
    category_dict = dict(category)
    del category_dict["id"]
    db_client.categories.update_one({"_id": ObjectId(category_id)}, {
        "$set": category_dict})
    updated_transaction = category_schema(
        db_client.categories.find_one({"_id": ObjectId(category_id)}))
    return Category(**updated_transaction)


@router.delete("/{transaction_id}", tags=["Transactions"])
async def delete_transaction(transaction_id: str, current_user: UserInDB = Depends(get_current_user)):
    db_client.transactions.delete_one({"_id": ObjectId(transaction_id)})
    return {"message": "Transaction deleted"}
