import datetime
from bson import ObjectId
from db.client import db_client


def format_datetime(dt):
    """Helper function to format datetime objects to ISO 8601 strings."""
    return dt.isoformat() if isinstance(dt, datetime.datetime) else None


def transaction_schema(transaction) -> dict:
    category = db_client.categories.find_one(
        {"_id": ObjectId(transaction['category_id'])})
    category_name = category["title"] if category else "Unknown Category"

    return {
        "id": str(transaction['_id']),
        "user_id": transaction["user_id"],
        "title": transaction["title"],
        "amount": str(transaction["amount"]),
        "account_id": str(transaction["account_id"]),
        "type": transaction["type"],
        "description": transaction["description"],
        "category_id": transaction["category_id"],
        "category_name": category_name,
        "createdAt": format_datetime(transaction.get("createdAt")),
        "updatedAt": format_datetime(transaction.get("updatedAt"))
    }
