def card_schema(card) -> dict:
    return {
        "id": str(card['_id']) if '_id' in card else None,
        "user_id": card["user_id"],
        "name": card["name"],
        "balance": card["balance"],
        "status": card["status"],
    }
