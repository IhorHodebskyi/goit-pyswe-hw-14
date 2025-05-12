from fastapi.params import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.schemas.user import UserShema
from src.repository.auth import get_user_by_email


async def update_avatar(email: str, url: str | None, db: AsyncSession = Depends(get_db)) -> UserShema:
    """
    Update the avatar for the user with the given email.

    Args:
        email (str): The email address of the user.
        url (str | None): The URL of the avatar to set. If None, the avatar will be cleared.
        db (AsyncSession, optional): The database session. Defaults to Depends(get_db).

    Returns:
        UserShema: The updated user.
    """
    user = await get_user_by_email(email=email, db=db)
    user.avatar = url
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user
