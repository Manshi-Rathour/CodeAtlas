from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_current_user
from app.core.security import hash_password, verify_password
from app.database.connection import get_db
from app.models.user import User
from app.schemas.auth import (
    PasswordChangeRequest,
    UserResponse,
    UserUpdate,
)
from app.services.source.storage_service import remove_user_storage


router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)


@router.patch(
    "/me",
    response_model=UserResponse,
)
def update_current_user(
    user_data: UserUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update the signed-in user's profile details.
    """

    full_name = user_data.full_name.strip()

    if len(full_name) < 2:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Full name must contain at least 2 characters.",
        )

    current_user.full_name = full_name

    try:
        db.commit()
        db.refresh(current_user)

        return current_user

    except Exception:
        db.rollback()
        raise


@router.post(
    "/me/password",
)
def change_password(
    password_data: PasswordChangeRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Change the signed-in user's password.

    The current password is required; no email verification is involved.
    """

    if not verify_password(
        password_data.current_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Current password is incorrect.",
        )

    if verify_password(
        password_data.new_password,
        current_user.hashed_password,
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The new password must be different.",
        )

    current_user.hashed_password = hash_password(
        password_data.new_password
    )

    try:
        db.commit()

        return {"message": "Password updated successfully."}

    except Exception:
        db.rollback()
        raise


@router.delete(
    "/me",
)
def delete_current_user(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Permanently delete the signed-in user's account and imported sources.
    """

    user_id = current_user.id

    try:
        db.delete(current_user)
        db.commit()

    except Exception:
        db.rollback()
        raise

    remove_user_storage(user_id)

    return {"message": "Account deleted successfully."}
