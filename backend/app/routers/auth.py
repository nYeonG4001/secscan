import secrets

from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.deps import get_current_user
from app.core.security import DUMMY_PASSWORD_HASH, create_access_token, verify_password
from app.models.user import User
from app.schemas.auth import AuthenticatedUserResponse, LoginRequest

router = APIRouter(prefix="/auth", tags=["auth"])


def _set_session_cookies(response: Response, *, session_token: str, csrf_token: str) -> None:
    common = {
        "max_age": settings.session_max_age_seconds,
        "secure": settings.SESSION_COOKIE_SECURE,
        "samesite": "strict",
        "path": "/",
    }
    response.set_cookie(
        settings.SESSION_COOKIE_NAME,
        session_token,
        httponly=True,
        **common,
    )
    response.set_cookie(
        settings.CSRF_COOKIE_NAME,
        csrf_token,
        httponly=False,
        **common,
    )


def _clear_session_cookies(response: Response) -> None:
    response.delete_cookie(
        settings.SESSION_COOKIE_NAME,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=True,
        samesite="strict",
        path="/",
    )
    response.delete_cookie(
        settings.CSRF_COOKIE_NAME,
        secure=settings.SESSION_COOKIE_SECURE,
        httponly=False,
        samesite="strict",
        path="/",
    )


@router.post("/login", response_model=AuthenticatedUserResponse)
def login(request: LoginRequest, response: Response, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == request.email).first()
    password_hash = user.password_hash if user else DUMMY_PASSWORD_HASH
    password_valid = verify_password(request.password, password_hash)
    if not user or not user.active or not password_valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="이메일 또는 비밀번호가 올바르지 않습니다.",
        )
    csrf_token = secrets.token_urlsafe(32)
    session_token = create_access_token({"sub": str(user.id), "csrf": csrf_token})
    _set_session_cookies(response, session_token=session_token, csrf_token=csrf_token)
    return AuthenticatedUserResponse(email=user.email, role=user.role)


@router.get("/me", response_model=AuthenticatedUserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return AuthenticatedUserResponse(email=current_user.email, role=current_user.role)


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(response: Response) -> None:
    _clear_session_cookies(response)
