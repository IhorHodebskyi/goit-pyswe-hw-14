from fastapi import Depends
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from libgravatar import Gravatar
from dotenv import load_dotenv
import logging

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserShema

load_dotenv()

logger = logging.getLogger(__name__)


async def get_user_by_email(email: str, db: AsyncSession = Depends(get_db)):
    """
    Get a user by their email address.

    Args:
        email (str): The user's email address.
        db (AsyncSession): The database session.

    Returns:
        User: The user.
    """
    stmt = select(User).filter_by(email=email)
    user = await db.execute(stmt)
    user = user.scalars().first()
    if not user:
        return None
    return user


async def create_user(body: UserShema, db: AsyncSession = Depends(get_db)):
    """
    Create a new user with the given email, username and password.

    Args:
        body (UserShema): The user's email, username and password.
        db (AsyncSession): The database session.

    Returns:
        User: The created user.
    """
    avatar = None
    try:
        g = Gravatar(body.email)
        avatar = g.get_image(default='404', size=500)
    except Exception as e:
        logger.error(f" Gravatar error {e}")
        pass
    new_user = User(
        **body.model_dump(),
        avatar=avatar
    )
    db.add(new_user)
    await db.commit()
    await db.refresh(new_user)
    return new_user


async def update_token(user: UserShema, refresh_token: str | None, db: AsyncSession = Depends(get_db)):
    """
    Update the refresh token for the given user.

    Args:
        user (UserShema): The user.
        refresh_token (str | None): The new refresh token.
        db (AsyncSession): The database session.

    Returns:
        None
    """
    user.refresh_token = refresh_token
    db.add(user)
    await db.commit()


async def confirmed_email(email: str, db: AsyncSession = Depends(get_db)) -> None:
    """
    Confirm the given user's email address.

    Args:
        email (str): The user's email address.
        db (AsyncSession): The database session.

    Returns:
        None
    """
    user = await get_user_by_email(email=email, db=db)
    user.confirmed = True
    db.add(user)
    await db.commit()


def repository_auth():
    return None