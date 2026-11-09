from fastapi import APIRouter, Response

from app.api.deps import CurrentUser, DbSession
from app.core.config import get_settings
from app.core.security import create_access_token
from app.schemas.auth import ChangePasswordRequest, LoginRequest, LoginResponse
from app.schemas.common import Message
from app.schemas.user import UserOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _cookie_args() -> dict:
    settings = get_settings()
    return {
        "key": settings.cookie_name,
        "httponly": True,
        "samesite": "lax",
        "secure": settings.cookie_secure,
        "path": "/",
    }


@router.post("/login", response_model=LoginResponse, summary="Sign in and start a session")
def login(data: LoginRequest, response: Response, db: DbSession) -> LoginResponse:
    user = auth_service.authenticate(db, data.username, data.password)
    token, lifetime = create_access_token(user.id)
    response.set_cookie(value=token, max_age=lifetime, **_cookie_args())
    return LoginResponse(user=UserOut.model_validate(user), expires_in=lifetime)


@router.post("/logout", response_model=Message, summary="End the session")
def logout(response: Response) -> Message:
    args = _cookie_args()
    response.delete_cookie(key=args["key"], path="/", httponly=True, samesite="lax", secure=args["secure"])
    return Message(message="Signed out.")


@router.get("/me", response_model=UserOut, summary="Current user")
def me(user: CurrentUser) -> UserOut:
    return UserOut.model_validate(user)


@router.post("/change-password", response_model=Message, summary="Change own password")
def change_password(data: ChangePasswordRequest, user: CurrentUser, db: DbSession) -> Message:
    auth_service.change_password(db, user, data.current_password, data.new_password)
    return Message(message="Password changed.")
