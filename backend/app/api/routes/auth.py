from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    UserSignup,
    UserLogin,
    AuthResponse,
    UserResponse
)
from app.core.security import (
    hash_password,
    verify_password,
    create_access_token
)
from app.api.dependencies import get_current_user


router = APIRouter(
    prefix="/api/auth",
    tags=["Authentication"]
)


@router.post(
    "/signup",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED
)
def signup(
    user_data: UserSignup,
    db: Session = Depends(get_db)
):

    existing_user = db.query(User).filter(
        User.email == user_data.email
    ).first()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An account with this email already exists."
        )

    new_user = User(
        full_name=user_data.full_name.strip(),
        email=user_data.email.lower(),
        hashed_password=hash_password(user_data.password)
    )

    try:
        db.add(new_user)
        db.commit()
        db.refresh(new_user)

        access_token = create_access_token(
            subject=str(new_user.id)
        )

        return {
            "user": new_user,
            "access_token": access_token,
            "token_type": "bearer"
        }

    except Exception:
        db.rollback()
        raise


@router.post(
    "/login",
    response_model=AuthResponse
)
def login(
    user_data: UserLogin,
    db: Session = Depends(get_db)
):

    user = db.query(User).filter(
        User.email == user_data.email.lower()
    ).first()

    if not user or not verify_password(
        user_data.password,
        user.hashed_password
    ):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password."
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Your account is inactive."
        )

    access_token = create_access_token(
        subject=str(user.id)
    )

    return {
        "user": user,
        "access_token": access_token,
        "token_type": "bearer"
    }


@router.get(
    "/me",
    response_model=UserResponse
)
def get_me(
    current_user: User = Depends(get_current_user)
):

    return current_user
