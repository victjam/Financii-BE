from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class Transaction(BaseModel):
    id: Optional[str] = None
    title: str
    user_id: Optional[str] = None
    account_id: str
    type: str
    amount: str
    description: str
    category_id: str
    category_name: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = None
