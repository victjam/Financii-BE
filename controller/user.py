from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException
from controller.auth import get_current_user
from models.user import User, UserInDB
from db.client import db_client
from db.schemas.user import user_schema
from bson import ObjectId
from passlib.context import CryptContext


router = APIRouter(prefix="/users", tags=["Users"])


bcrypt_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

PREDEFINED_BALANCE = 0.0
PREDEFINED_CATEGORIES = ["Groceries", "Utilities",
                         "Rent", "Entertainment", "Transportation"]


@router.post("/", tags=["Users"])
async def create_user(user: User):
    user_dict = dict(user)
    if not user_dict.get("password"):
        raise HTTPException(status_code=400, detail="Password is required")
    hashed_password = bcrypt_context.hash(user_dict["password"])
    user_dict["password"] = hashed_password
    user_dict["updatedAt"] = None
    existing_user = db_client.users.find_one({
        "$or": [{"email": user.email}, {"username": user.username}]
    })
    if existing_user:
        if existing_user.get("email") == user.email:
            raise HTTPException(status_code=400, detail="Email already taken")
        elif existing_user.get("username") == user.username:
            raise HTTPException(
                status_code=400, detail="Username already taken")
    del user_dict["id"]  # Ensure this line is before inserting to database
    user_id = db_client.users.insert_one(user_dict).inserted_id
    new_user = user_schema(db_client.users.find_one({"_id": user_id}))

    # Create a default account with a predefined balance
    default_account = {
        "user_id": str(user_id),
        "name": "Default Account",
        "type": "checking",
        "balance": PREDEFINED_BALANCE,
        "createdAt": datetime.now()
    }
    db_client.accounts.insert_one(default_account)

    # Create predefined categories
    for category_title in PREDEFINED_CATEGORIES:
        category = {
            "title": category_title,
            "user_id": str(user_id),
            "createdAt": datetime.now()
        }
        db_client.categories.insert_one(category).inserted_id

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
async def update_user(user_id: str, user: User, current_user: UserInDB = Depends(get_current_user)):
    if str(current_user.id) != user_id:
        raise HTTPException(
            status_code=403, detail="Unauthorized to update this user.")

    update_data = user.dict(exclude_unset=True, exclude={
                            'id', 'createdAt', 'password'})

    if user.password:
        hashed_password = bcrypt_context.hash(user.password)
        update_data['password'] = hashed_password

    # Always update the 'updatedAt' field to the current timestamp
    update_data['updatedAt'] = datetime.now()

    # Update the user data in the database
    result = db_client.users.update_one(
        {"_id": ObjectId(user_id)}, {"$set": update_data}
    )

    if result.matched_count == 0:
        raise HTTPException(status_code=404, detail="User not found")

    # Retrieve the updated user information
    updated_user = db_client.users.find_one({"_id": ObjectId(user_id)})
    if not updated_user:
        raise HTTPException(status_code=404, detail="Updated user not found")

    # Return the updated user information
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
