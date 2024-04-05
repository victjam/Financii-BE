import datetime
from pydantic import BaseModel
from typing import Optional


class Category(BaseModel):
    id: Optional[str] = None
    title: str
    user_id: str
    date: datetime.datetime
