def user_schema(user) -> dict:
    return {
        "id": str(user['_id']) if '_id' in user else None,
        "username": user["username"],
        "first_name": user["first_name"],
        "last_name": user["last_name"],
        "email": user["email"],
    }
