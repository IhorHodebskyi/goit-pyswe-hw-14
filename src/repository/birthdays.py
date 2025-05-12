from datetime import datetime, timedelta
from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from src.entity.models import Contact
from src.database.db import get_db




async def get_upcoming_birthdays(db: AsyncSession = Depends(get_db)):
    """
    Get a list of contacts that have a birthday in the next 7 days.

    Args:
        db (AsyncSession): The database session to use.

    Returns:
        list[Contact]: A list of contacts with a birthday in the next 7 days.
    """
    today = datetime.today().date()
    in_7_days = today + timedelta(days=7)
    result = await db.execute(select(Contact))
    users = result.scalars().all()
    upcoming = []
    for user in users:
        if not user.birthday:
            continue
        birthday = user.birthday
        bday_this_year = birthday.replace(year=today.year)

        if bday_this_year < today:
            bday_this_year = bday_this_year.replace(year=today.year + 1)

        if today <= bday_this_year <= in_7_days:
            upcoming.append(user)

    return upcoming
