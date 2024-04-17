from fastapi import APIRouter, Depends, HTTPException, Query
from typing import List, Optional
from models.category import Category
from controller.auth import get_current_user
from db.client import db_client
from db.schemas.category import category_schema
from bson import ObjectId
from datetime import datetime, timedelta

from models.user import UserInDB

router = APIRouter(prefix="/categories", tags=["Categories"])


def parse_datetime(date_str: str) -> datetime:
    """Parse the incoming date string to datetime, assuming UTC."""
    return datetime.fromisoformat(date_str.replace("Z", "+00:00"))


@router.post("/", response_model=Category)
async def create_category(category: Category, current_user: UserInDB = Depends(get_current_user)):
    category_dict = category.model_dump(exclude_unset=True)
    category_dict["user_id"] = current_user.id
    category_dict["createdAt"] = datetime.now()
    category_dict["updatedAt"] = None

    # Insert the new category into the database
    result = db_client.categories.insert_one(category_dict)
    if result.inserted_id is None:
        raise HTTPException(
            status_code=500, detail="Error al crear la categoría")

    # Retrieve and return the newly created category
    new_category = db_client.categories.find_one({"_id": result.inserted_id})
    if not new_category:
        raise HTTPException(
            status_code=404, detail="Nueva categoría no encontrada")

    return category_schema(new_category)


@router.get("/", tags=["Categories"])
async def get_categories(current_user: UserInDB = Depends(get_current_user),
                         startDate: Optional[str] = Query(None),
                         endDate: Optional[str] = Query(None)):
    try:
        if startDate and endDate:
            start_datetime = parse_datetime(startDate)
            end_datetime = parse_datetime(endDate)

            # Expand end_datetime by one second to ensure inclusion of categories at the exact end time
            end_datetime += timedelta(seconds=1)

            query = {
                "user_id": current_user.id,
                "createdAt": {"$gte": start_datetime, "$lt": end_datetime}
            }
        else:
            query = {"user_id": current_user.id}

        categories = db_client.categories.find(query)
        return [Category(**category_schema(category)) for category in categories]
    except Exception as e:
        raise HTTPException(
            status_code=500, detail="Ha ocurrido un error: " + str(e))


@router.put("/{category_id}", tags=["Categories"])
async def update_category(category_id: str, category: Category, current_user: UserInDB = Depends(get_current_user)):
    existing_category = db_client.categories.find_one(
        {"_id": ObjectId(category_id), "user_id": current_user.id})
    if not existing_category:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    update_data = category.model_dump(
        exclude_unset=True, exclude={"createdAt", "id"})
    update_data["updatedAt"] = datetime.now()

    db_client.categories.update_one(
        {"_id": ObjectId(category_id), "user_id": current_user.id},
        {"$set": update_data}
    )

    updated_category = db_client.categories.find_one(
        {"_id": ObjectId(category_id)})
    return category_schema(updated_category)


@router.delete("/{category_id}", tags=["Categories"])
async def delete_category(category_id: str, current_user: UserInDB = Depends(get_current_user)):
    if db_client.transactions.count_documents({"category_id": category_id}) > 0:
        raise HTTPException(
            status_code=400, detail="No se puede eliminar una categoria asociada a transacciones existentes")

    result = db_client.categories.delete_one(
        {"_id": ObjectId(category_id), "user_id": current_user.id})
    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="Categoria no encontrada")

    return {"message": "Categoria Eliminada"}
