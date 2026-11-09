import re
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from app.models.enums import Role
from app.schemas.common import ORMModel, text

USERNAME_RE = re.compile(r"^[a-z0-9_.-]{3,32}$")
MIN_PASSWORD_LENGTH = 10


def validate_password_strength(value: str) -> str:
    if len(value) < MIN_PASSWORD_LENGTH:
        raise ValueError(f"Password must be at least {MIN_PASSWORD_LENGTH} characters long.")
    if len(value) > 128:
        raise ValueError("Password must be at most 128 characters long.")
    if value.lower() == value or value.upper() == value or not any(c.isdigit() for c in value):
        raise ValueError("Password must contain upper-case and lower-case letters and a digit.")
    return value


def normalize_username(value: str) -> str:
    value = value.strip().lower()
    if not USERNAME_RE.match(value):
        raise ValueError("Username must be 3-32 characters: letters, digits, dot, dash or underscore.")
    return value


class UserBrief(ORMModel):
    id: int
    username: str
    display_name: str


class UserOut(ORMModel):
    id: int
    username: str
    display_name: str
    role: Role
    is_active: bool
    created_at: datetime
    updated_at: datetime


class UserCreate(BaseModel):
    username: str
    display_name: text(2, 80)
    password: str
    role: Role = Role.WORKER

    _username = field_validator("username")(normalize_username)
    _password = field_validator("password")(validate_password_strength)


class UserUpdate(BaseModel):
    display_name: text(2, 80) | None = None
    role: Role | None = None
    password: str | None = Field(default=None, description="Set a new password (admin reset).")

    @field_validator("password")
    @classmethod
    def _password(cls, value: str | None) -> str | None:
        return validate_password_strength(value) if value is not None else None
