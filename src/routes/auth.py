from fastapi import APIRouter, Depends, HTTPException, status, Security, requests, Request
from fastapi.security import OAuth2PasswordRequestForm, HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from fastapi import BackgroundTasks

from src.database.db import get_db
from src.repository import auth as repository_auth
from src.schemas.user import UserShema, UserResponse, TokenShema, RequestEmail
from src.services.auth import auth_service
from src.services.email import send_email
from src.conf import messages

router = APIRouter(prefix="/auth", tags=["auth"])

get_refresh_token = HTTPBearer()


@router.post("/signup", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def signup(body: UserShema, bt: BackgroundTasks, request: Request, db: Session = Depends(get_db)):
    """
    Create a new user with the given email, username and password.

    Args:
    body (UserShema): The user's email, username and password.
    bt (BackgroundTasks): The background tasks to add the email sending task to.
    request (Request): The current request.
    db (Session): The database session.

    Raises:
    HTTPException: If the given email already exists.

    Returns:
    UserResponse: The created user.
    """
    exist_user = await repository_auth.get_user_by_email(email=body.email, db=db)
    if exist_user:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=messages.ACCOUNT_EXISTS)
    body.password = auth_service.get_password_hash(body.password)
    new_user = await repository_auth.create_user(body=body, db=db)
    bt.add_task(send_email, new_user.email, new_user.username, str(request.base_url))
    return new_user


@router.post("/login", response_model=TokenShema, status_code=status.HTTP_200_OK)
async def login(body: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(get_db)):
    """
    Login a user with the given email and password.

    Args:
    body (OAuth2PasswordRequestForm): The user's email and password.
    db (Session): The database session.

    Raises:
    HTTPException: If the given email or password is invalid.
    If the email is not confirmed.

    Returns:
    TokenShema: The access and refresh tokens.
    """
    user = await repository_auth.get_user_by_email(email=body.username, db=db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.CREDENTIALS_EXCEPTION)
    if not user.confirmed:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.EMAIL_NOT_CONFIRMED)
    if not auth_service.verify_password(body.password, user.password):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=messages.CREDENTIALS_EXCEPTION)
    access_token = await auth_service.create_access_token(data={"sub": user.email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": user.email})
    await repository_auth.update_token(user=user, refresh_token=refresh_token, db=db)
    await db.commit()
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/refresh_token', response_model=TokenShema, status_code=status.HTTP_200_OK)
async def refresh_token(credentials: HTTPAuthorizationCredentials = Security(get_refresh_token),
                        db: Session = Depends(get_db)):
    """
    Get a new access and refresh token from a refresh token.

    Args:
    credentials (HTTPAuthorizationCredentials): The refresh token to use.
    db (Session): The database session.

    Raises:
    HTTPException: If the given refresh token is invalid or has an invalid scope.
    If the email associated with the refresh token is not confirmed.
    If the refresh token is invalid.

    Returns:
    TokenShema: The new access and refresh tokens.
    """
    token = credentials.credentials
    email = await auth_service.decode_refresh_token(token)
    user = await repository_auth.get_user_by_email(email=email, db=db)
    if user.refresh_token != token:
        await repository_auth.update_token(user=user, refresh_token=None, db=db)
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid refresh token")
    access_token = await auth_service.create_access_token(data={"sub": email})
    refresh_token = await auth_service.create_refresh_token(data={"sub": email})
    await repository_auth.update_token(user=user, refresh_token=refresh_token, db=db)
    return {"access_token": access_token, "refresh_token": refresh_token, "token_type": "bearer"}


@router.get('/confirmed_email/{token}', status_code=status.HTTP_200_OK)
async def confirmed_email(token: str, db: Session = Depends(get_db)):
    """
    Confirm a user's email by verifying the given token.

    Args:
        token (str): The verification token to use.
        db (Session): The database session.

    Raises:
        HTTPException: If the given token is invalid or has an invalid scope.
        If the email associated with the token is not confirmed.
        If the token is invalid.

    Returns:
        dict: A dictionary containing a message indicating whether the email was confirmed or not.
    """
    email = await auth_service.get_email_from_token(token)
    user = await repository_auth.get_user_by_email(email, db)
    if user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=messages.VERIFICATION_ERROR)
    if user.confirmed:
        return {"message": "Your email is already confirmed"}
    await repository_auth.confirmed_email(email, db)
    return {"message": "Email confirmed"}


@router.post('/request_email', status_code=status.HTTP_200_OK)
async def request_email(body: RequestEmail, background_tasks: BackgroundTasks, request: Request,
                        db: Session = Depends(get_db)):
    """
    Request a verification email for a user.

    Args:
        body (RequestEmail): The user's email.
        background_tasks (BackgroundTasks): The background tasks to add the email sending task to.
        request (Request): The current request.
        db (Session): The database session.

    Returns:
        dict: A dictionary containing a message indicating whether the email was sent or not.
    """
    user = await repository_auth.get_user_by_email(body.email, db)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=messages.USER_NOT_FOUND)
    if user.confirmed:
        return {"message": messages.YOUR_EMAIL_IS_ALREADY_CONFIRMED}
    if user:
        background_tasks.add_task(send_email, user.email, user.username, str(request.base_url))
    return {"message": messages.CHECK_EMAIL}
