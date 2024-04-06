from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional


class Category(BaseModel):
    id: Optional[str] = None
    title: str
    user_id: Optional[str] = None
    createdAt: datetime = Field(default_factory=datetime.now)
    updatedAt: Optional[datetime] = None
