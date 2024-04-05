import datetime
from pydantic import BaseModel
from typing import Optional


class Transaction(BaseModel):
    id: Optional[str] = None
    title: str
    user_id: str
    amount: str
    date: datetime.datetime
    description: str
    category_id: str
    category_name: Optional[str] = None
