from fastapi import APIRouter, Depends, status, File, UploadFile

from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.db import get_db
from src.entity.models import User
from src.schemas.user import UserResponse
from src.services.auth import auth_service
from src.conf.config import config
from src.repository import users as repository_users

import cloudinary
import cloudinary.uploader

router = APIRouter(prefix="/users", tags=["users"])

cloudinary.config(
    cloud_name=config.CLOUDINARY_NAME,
    api_key=config.CLOUDINARY_API_KEY,
    api_secret=config.CLOUDINARY_API_SECRET,
    secure=True
)


@router.get("/", response_model=UserResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def get_current_user(current_user: User = Depends(auth_service.get_current_user)):
    """
    Retrieve the current user.

    This endpoint returns the current authenticated user.

    Returns:
        UserResponse: The current user.
    """
    return current_user


@router.put("/avatar", response_model=UserResponse, status_code=status.HTTP_200_OK,
            dependencies=[Depends(RateLimiter(times=1, seconds=20))])
async def upload_avatar(file: UploadFile = File(), db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(auth_service.get_current_user)):
    """
    Uploads and updates the avatar for the current user.

    This endpoint allows the current authenticated user to upload a new avatar image.
    The image is uploaded to Cloudinary, and the user's avatar URL is updated in the database.

    Args:
        file (UploadFile): The avatar image file to be uploaded.
        db (AsyncSession): The database session.
        current_user (User): The current authenticated user.

    Returns:
        UserResponse: The updated user with the new avatar URL.
    """

    public_id = f"avatar/{current_user.email}"
    upload_result = cloudinary.uploader.upload(file.file, public_id=public_id, overwrite=True)
    current_user.avatar_url = cloudinary.CloudinaryImage(public_id).build_url(
        width=250, height=250, crop="fill", gravity="face", radius=40, corp="fill", version=upload_result.get("version")
    )

    new_user = await repository_users.update_avatar(email=current_user.email, url=upload_result.get("url"), db=db)

    return new_user
