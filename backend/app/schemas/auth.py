from pydantic import BaseModel, EmailStr, Field


class UserSignup(BaseModel):
    full_name: str = Field(
        min_length=2,
        max_length=100
    )

    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


class UserLogin(BaseModel):
    email: EmailStr

    password: str = Field(
        min_length=8,
        max_length=128
    )


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: int
    full_name: str
    email: EmailStr
    is_active: bool

    model_config = {
        "from_attributes": True
    }


class AuthResponse(BaseModel):
    user: UserResponse
    access_token: str
    token_type: str = "bearer"
