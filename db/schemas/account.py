
import datetime


def format_datetime(dt):
    """Helper function to format datetime objects to ISO 8601 strings."""
    return dt.isoformat() if isinstance(dt, datetime.datetime) else None


def account_schema(account) -> dict:
    return {
        "id": str(account["_id"]),
        "user_id": str(account["user_id"]),
        "name": account["name"],
        "type": account["type"],
        "balance": account["balance"],
        "createdAt": format_datetime(account.get("createdAt")),
        "updatedAt": format_datetime(account.get("updatedAt"))
    }
