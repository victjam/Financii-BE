def category_schema(category) -> dict:
    return {
        "id": str(category['_id']) if '_id' in category else None,
        "user_id": category["user_id"],
        "title": category["title"],
        "date": category["date"].strftime('%Y-%m-%d %H:%M:%S') if category.get("date") else None,
    }
