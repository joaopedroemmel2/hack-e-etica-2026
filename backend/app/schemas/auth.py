from pydantic import EmailStr, Field

from app.schemas.common import APIModel, UserPublic


class RegisterRequest(APIModel):
    name: str = Field(min_length=2, max_length=120)
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class LoginRequest(APIModel):
    email: EmailStr
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(APIModel):
    refresh_token: str


class ChangePasswordRequest(APIModel):
    current_password: str = Field(min_length=8, max_length=128)
    new_password: str = Field(min_length=8, max_length=128)


class TokenPair(APIModel):
    access_token: str
    refresh_token: str


class AuthResponse(TokenPair):
    user: UserPublic
