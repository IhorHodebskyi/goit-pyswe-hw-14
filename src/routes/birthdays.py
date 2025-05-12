from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.repository import birthdays as repository_birthdays
from src.schemas.contact import  ContactResponse

router = APIRouter(prefix="/birthdays", tags=["birthdays"])

@router.get("/upcoming_birthdays", response_model=list[ContactResponse])
async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    """
    Get list of users whose birthday is in the next 7 days
    """
    users = await repository_birthdays.get_upcoming_birthdays(db=db)
    return users

