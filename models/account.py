from pydantic import BaseModel
from typing import Optional


class Account(BaseModel):
    id: Optional[str] = None
    user_id: str
    name: str
    type: str
    balance: float = 0.0
