from datetime import datetime, timedelta
from typing import Optional
import json
from fastapi import Depends, HTTPException, status
from passlib.context import CryptContext
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session
from jose import JWTError, jwt
import redis
import pickle

from src.database.db import get_db
from src.repository import auth as repository_auth
from src.conf.config import config

from dotenv import load_dotenv
import logging

load_dotenv()

logger = logging.getLogger(__name__)


class Auth:
    pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
    SECRET_KEY = config.JWT_SECRET_KEY
    ALGORITHM = config.JWT_ALGORITHM
    cache = redis.Redis(host=config.REDIS_DOMAIN,
                        port=config.REDIS_PORT,
                        db=0,
                        password=config.REDIS_PASSWORD,
                        )

    def verify_password(self, plain_password, hashed_password):
        """
        Verifies a plain password against a hashed password.

        Args:
            plain_password (str): The plain password to be verified.
            hashed_password (str): The hashed password to be verified against.

        Returns:
            bool: True if the passwords match, False if they don't.
        """
        return self.pwd_context.verify(plain_password, hashed_password)

    def get_password_hash(self, password: str):
        return self.pwd_context.hash(password)

    oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/auth/login")

    async def create_access_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates an access token.

        Args:
            data (dict): The data to encode in the token.
            expires_delta (Optional[float]): The time delta until the token expires. Defaults to 15 minutes.

        Returns:
            str: The encoded access token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(minutes=15)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "access_token"})
        encoded_access_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_access_token

    async def create_refresh_token(self, data: dict, expires_delta: Optional[float] = None):
        """
        Creates a refresh token.

        Args:
            data (dict): The data to encode in the token.
            expires_delta (Optional[float]): The time delta until the token expires. Defaults to 7 days.

        Returns:
            str: The encoded refresh token.
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.now() + timedelta(seconds=expires_delta)
        else:
            expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire, "scope": "refresh_token"})
        encoded_refresh_token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return encoded_refresh_token

    async def decode_refresh_token(self, refresh_token: str):
        """
        Decodes a refresh token.

        Args:
            refresh_token (str): The token to decode.

        Returns:
            str: The email associated with the token.

        Raises:
            HTTPException: If the token is invalid or has an invalid scope.
        """
        try:
            payload = jwt.decode(refresh_token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'refresh_token':
                email = payload['sub']
                return email
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Invalid scope for token')
        except JWTError:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Could not validate credentials')

    async def get_current_user(self, token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
        """
        Gets the current user using the provided token.

        Args:
            token (str): The token to decode.
            db (Session): The database session.

        Returns:
            User: The current user.

        Raises:
            HTTPException: If the token is invalid or has an invalid scope.
        """
        credentials_exception = HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )

        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            if payload['scope'] == 'access_token':
                email = payload["sub"]
                if email is None:
                    raise credentials_exception
            else:
                raise credentials_exception
        except JWTError as e:
            raise credentials_exception

        user_hash = str(email)

        user = self.cache.get(user_hash)
        if user is None:
            user = await repository_auth.get_user_by_email(email=email, db=db)
            if user is None:
                raise credentials_exception
            self.cache.set(user_hash, pickle.dumps(user))
            self.cache.expire(user_hash, 300)
        else:
            try:
                user = pickle.loads(user)
            except (pickle.UnpicklingError, EOFError) as e:
                raise credentials_exception

        return user

    def create_email_token(self, data: dict):
        """
        Creates a token for email verification.

        Args:
            data (dict): The data to encode in the token.

        Returns:
            str: The encoded token.

        Notes:
            The token is valid for 7 days.
        """
        to_encode = data.copy()
        expire = datetime.now() + timedelta(days=7)
        to_encode.update({"iat": datetime.now(), "exp": expire})
        token = jwt.encode(to_encode, self.SECRET_KEY, algorithm=self.ALGORITHM)
        return token

    async def get_email_from_token(self, token: str):
        try:
            payload = jwt.decode(token, self.SECRET_KEY, algorithms=[self.ALGORITHM])
            email = payload["sub"]
            return email
        except JWTError as e:
            logger.error(f"Error in get_email_from_token {e}")
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                                detail="Invalid token for email verification")


auth_service = Auth()
