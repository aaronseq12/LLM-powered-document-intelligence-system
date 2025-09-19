"""
Authentication and Authorization Service

This module handles JWT token creation and validation, providing security
for the application's API endpoints.
"""

from datetime import datetime, timedelta
from typing import Optional

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from pydantic import BaseModel

from config import settings

# This scheme will require a token to be sent in the Authorization header
# as a "Bearer" token.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


class TokenData(BaseModel):
    username: Optional[str] = None


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
    """Creates a new JWT access token."""
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(
            minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
        )

    to_encode.update({"exp": expire})
    encoded_jwt = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=settings.JWT_ALGORITHM
    )
    return encoded_jwt


def get_current_user(token: str = Depends(oauth2_scheme)):
    """
    Validates the token and returns the current user.
    For this example, we'll just decode the username from the token.
    """
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.JWT_ALGORITHM]
        )
        username: str = payload.get("sub")
        if username is None:
            raise credentials_exception
        # In a real app, you would fetch the user from the database here.
        return username
    except JWTError:
        raise credentials_exception
