from pydantic import BaseModel, Field, field_validator

from app.schemas.user import UserOut, validate_password_strength


class LoginRequest(BaseModel):
    username: str = Field(min_length=1, max_length=64)
    password: str = Field(min_length=1, max_length=128)

    @field_validator("username")
    @classmethod
    def _clean(cls, value: str) -> str:
        return value.strip().lower()


class LoginResponse(BaseModel):
    user: UserOut
    expires_in: int


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1, max_length=128)
    new_password: str

    _strength = field_validator("new_password")(validate_password_strength)
