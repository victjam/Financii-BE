
def account_schema(account) -> dict:
    return {
        "id": str(account["_id"]),
        "user_id": str(account["user_id"]),
        "name": account["name"],
        "type": account["type"],
        "balance": account["balance"]
    }
