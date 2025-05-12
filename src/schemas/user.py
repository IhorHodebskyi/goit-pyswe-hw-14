from pydantic import BaseModel, EmailStr, Field
from typing import Optional


class UserShema(BaseModel):
    username: str = Field(..., max_length=150, min_length=1)
    email: EmailStr = Field(..., max_length=150, min_length=1)
    password: str = Field(..., min_length=6, max_length=8)

class UserResponse(BaseModel):
    id: int = Field(..., gt=0)
    username: str = Field(..., max_length=150, min_length=1)
    email: EmailStr = Field(..., max_length=150, min_length=1)
    avatar: Optional[str] = None

    class Config:
        from_attributes = True

class TokenShema(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "Bearer"


class RequestEmail(BaseModel):
    email: EmailStr