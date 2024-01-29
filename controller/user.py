from fastapi import APIRouter, HTTPException
from models.user import User
from db.client import db_client
from db.schemas.user import user_schema
from bson import ObjectId
from passlib.context import CryptContext

import random
import string

router = APIRouter(prefix="/users")


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def random_string(length: int) -> str:
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


@router.post("/", tags=["Users"])
async def create_user(user: User):
    user_dict = dict(user)
    if not user_dict.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")
    hashed_password = bcrypt_context.hash(user_dict["password"])
    user_dict["password"] = hashed_password
    existing_user = db_client.users.find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })
    if existing_user:
        if existing_user.get("email") == user.email:
            raise HTTPException(status_code=400, detail="Email already taken")
        elif existing_user.get("username") == user.username:
            raise HTTPException(
                status_code=400, detail="Username already taken")
    del user_dict["id"]
    id = db_client.users.insert_one(user_dict).inserted_id
    new_user = user_schema(db_client.users.find_one({"_id": id}))
    return User(**new_user)


@router.get("/{user_id}", tags=["Users"])
async def read_user(user_id: str):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=404, detail="Invalid user ID format")

    user = db_client.users.find_one({"_id": oid})
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return User(**user_schema(user))


@router.get("/", tags=["Users"])
async def read_user():
    users = db_client.users.find()
    return [User(**user_schema(user)) for user in users]


@router.put("/{user_id}", tags=["Users"])
async def update_user(user_id: str, user: User):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    existing_user = db_client.users.find_one({"_id": oid})
    if not existing_user:
        raise HTTPException(status_code=404, detail="User not found")

    user_dict = user.dict(exclude_unset=True)
    if "id" in user_dict:
        del user_dict["id"]

    if "password" in user_dict and user_dict["password"] is None:
        del user_dict["password"]

    db_client.users.update_one({"_id": oid}, {"$set": user_dict})

    updated_user = db_client.users.find_one({"_id": oid})
    return user_schema(updated_user)


@router.delete("/{user_id}", tags=["Users"])
async def delete_user(user_id: str):
    try:
        oid = ObjectId(user_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid user ID format")

    result = db_client.users.delete_one({"_id": oid})

    if result.deleted_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    return {"message": "User successfully deleted"}
