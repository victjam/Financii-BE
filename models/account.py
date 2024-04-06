from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class Account(BaseModel):
    id: Optional[str] = None
    user_id: Optional[str] = None
    name: str
    type: str
    balance: float = 0.0
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = None
