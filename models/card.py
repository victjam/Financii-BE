from pydantic import BaseModel
from typing import Optional


class Card(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    balance: float
    status: str
