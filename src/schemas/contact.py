from pydantic import BaseModel, EmailStr, Field
from datetime import date, datetime
from typing import Optional
from src.schemas.user import UserResponse


class ContactShema(BaseModel):
    name: str = Field(..., max_length=150, min_length=1)
    surname: str = Field(..., min_length=1, max_length=150)
    email: EmailStr
    phone: str = Field(..., min_length=5, max_length=20)
    birthday: Optional[date] = None
    additional_data: Optional[str] = None


class ContactResponse(ContactShema):
    id: int = Field(..., gt=0)
    created_at: datetime
    updated_at: datetime
    user: Optional[UserResponse] = None

    class Config:
        from_attributes = True
