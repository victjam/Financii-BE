from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class User(BaseModel):
    id: Optional[str] = None
    username: str
    first_name: str
    last_name: str
    email: str
    password: Optional[str] = None
    disabled: Optional[bool] = False
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = None


class UserInDB(User):
    hashed_password: str
