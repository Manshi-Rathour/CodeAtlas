from datetime import datetime, timedelta, timezone

import jwt
from pwdlib import PasswordHash

from app.core.config import settings


# Initialize Argon2 password hashing.
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """
    Hash a plain-text password using Argon2.
    """
    return password_hasher.hash(password)


def verify_password(
    plain_password: str,
    hashed_password: str
) -> bool:
    """
    Verify a password against its stored hash.
    """
    return password_hasher.verify(
        plain_password,
        hashed_password
    )


def create_access_token(subject: str) -> str:
    """
    Generate a JWT access token for a user.
    """

    expiration = datetime.now(timezone.utc) + timedelta(
        minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )

    payload = {
        "sub": subject,
        "exp": expiration
    }

    token = jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm=settings.ALGORITHM
    )

    return token


def decode_access_token(token: str):
    """
    Decode and validate a JWT token.

    Returns the token payload if valid,
    otherwise returns None.
    """

    try:
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )

        return payload

    except jwt.InvalidTokenError:
        return None
