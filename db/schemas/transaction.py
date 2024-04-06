
from bson import ObjectId
from db.client import db_client


def transaction_schema(transaction) -> dict:
    category = db_client.categories.find_one(
        {"_id": ObjectId(transaction['category_id'])})

    category_name = category["title"] if category else "Unknown Category"
    return {
        "id": str(transaction['_id']) if '_id' in transaction else None,
        "user_id": transaction["user_id"],
        "title": transaction["title"],
        "amount": str(transaction["amount"]),
        "account_id": str(transaction["account_id"]),
        "date": transaction["date"],
        "type": transaction["type"],
        "description": transaction["description"],
        "category_id": transaction["category_id"],
        "category_name": category_name,

    }
