from fastapi import APIRouter, Depends, status, Response
from sqlalchemy.orm import Session
from fastapi.responses import FileResponse

from src.database.db import get_db
from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/amail_tracking", tags=["email_tracking"])


@router.get("/{username}", response_class=FileResponse, status_code=status.HTTP_200_OK)
async def email_tracker(username: str, response: Response, db: Session = Depends(get_db)):
    """
    Endpoint for tracking email openning.

    This endpoint will be used to track whether the user has opened the email or not.

    Args:
        username (str): The username of the user.
        response (Response): The response object.
        db (Session, optional): The database session. Defaults to Depends(get_db).

    Returns:
        FileResponse: A FileResponse object containing the image.
    """
    logger.info(f"email_tracker {username}")
    return FileResponse("src/static/open_check.png", media_type="image/png", content_disposition_type="inline")
