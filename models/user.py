from pydantic import BaseModel
from typing import Optional


class User(BaseModel):
    id: Optional[str] = None
    username: str
    first_name: str
    last_name: str
    email: str
    password: Optional[str] = None
    disabled: Optional[bool] = False


class UserInDB(User):
    hashed_password: str
