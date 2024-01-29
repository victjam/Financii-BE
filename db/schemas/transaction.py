def transaction_schema(transaction) -> dict:
    return {
        "id": str(transaction['_id']) if '_id' in transaction else None,
        "user_id": transaction["user_id"],
        "title": transaction["title"],
        "amount": str(transaction["amount"]),
        "date": transaction["date"],
        "description": transaction["description"],
        # "category": transaction["category"],
        # "status": transaction["status"],
    }
