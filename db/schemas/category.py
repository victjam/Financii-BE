import datetime


def format_datetime(dt):
    """Helper function to format datetime objects to ISO 8601 strings."""
    return dt.isoformat() if isinstance(dt, datetime.datetime) else None


def category_schema(category) -> dict:
    return {
        "id": str(category['_id']),
        "user_id": category["user_id"],
        "title": category["title"],
        "createdAt": format_datetime(category.get("createdAt")),
        "updatedAt": format_datetime(category.get("updatedAt")),
    }
