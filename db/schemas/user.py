import datetime


def format_datetime(dt):
    """Helper function to format datetime objects to ISO 8601 strings."""
    return dt.isoformat() if isinstance(dt, datetime.datetime) else None


def user_schema(user) -> dict:
    return {
        "id": str(user['_id']),
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
        "createdAt": format_datetime(user.get("createdAt")),
        "updatedAt": format_datetime(user.get("updatedAt")),
    }
