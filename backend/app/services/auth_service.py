from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import UnauthorizedError
from app.core.security import hash_password, password_needs_rehash, verify_password
from app.models.user import User

INVALID_LOGIN = "Invalid username or password."


def authenticate(db: Session, username: str, password: str) -> User:
    """Return the user for valid credentials.

    The same error is used for an unknown user, a wrong password and an inactive account so
    that the response does not reveal which one it was.
    """
    user = db.scalar(select(User).where(User.username == username))
    password_ok = verify_password(password, user.password_hash if user else None)
    if user is None or not password_ok or not user.is_active:
        raise UnauthorizedError(INVALID_LOGIN, code="invalid_credentials")
    if password_needs_rehash(user.password_hash):
        user.password_hash = hash_password(password)
        db.commit()
    return user


def change_password(db: Session, user: User, current_password: str, new_password: str) -> None:
    if not verify_password(current_password, user.password_hash):
        raise UnauthorizedError("The current password is not correct.", code="invalid_credentials")
    user.password_hash = hash_password(new_password)
    db.commit()
