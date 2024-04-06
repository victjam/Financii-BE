import datetime
from pydantic import BaseModel
from typing import Optional


class Transaction(BaseModel):
    id: Optional[str] = None
    title: str
    user_id: str
    account_id: str
    type: str
    amount: str
    date: datetime.datetime
    description: str
    category_id: str
    category_name: Optional[str] = None
