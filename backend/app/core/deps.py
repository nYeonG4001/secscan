import hmac
from functools import lru_cache
from pathlib import Path

import jwt
from fastapi import Cookie, Depends, Header, HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.core.security import decode_access_token
from app.services.project_upload_lock import ProjectUploadLocks
from app.services.source_workspace import SourceWorkspace

INVALID_SESSION_DETAIL = "인증 정보가 유효하지 않습니다."
PROJECT_NOT_FOUND_DETAIL = "프로젝트를 찾을 수 없습니다."


def _unauthorized() -> HTTPException:
    return HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail=INVALID_SESSION_DETAIL,
    )


def get_current_user(
    session_token: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    db: Session = Depends(get_db),
):
    from app.models.user import User

    try:
        if not session_token:
            raise ValueError
        payload = decode_access_token(session_token)
        subject = payload["sub"]
        if not isinstance(subject, str) or not subject.isdecimal() or int(subject) <= 0:
            raise ValueError
        user_id = int(subject)
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized()
    user = db.get(User, user_id)
    if not user or not user.active:
        raise _unauthorized()
    return user


def require_csrf(
    session_token: str | None = Cookie(default=None, alias=settings.SESSION_COOKIE_NAME),
    csrf_cookie: str | None = Cookie(default=None, alias=settings.CSRF_COOKIE_NAME),
    csrf_header: str | None = Header(default=None, alias="X-CSRF-Token"),
) -> None:
    """Require a header value bound to the authenticated session's CSRF claim."""
    try:
        if not session_token:
            raise ValueError
        payload = decode_access_token(session_token)
        csrf_claim = payload["csrf"]
        if not isinstance(csrf_claim, str):
            raise ValueError
    except (jwt.PyJWTError, KeyError, ValueError):
        raise _unauthorized()

    if not (
        csrf_cookie
        and csrf_header
        and hmac.compare_digest(csrf_header, csrf_cookie)
        and hmac.compare_digest(csrf_header, csrf_claim)
    ):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="CSRF 토큰이 유효하지 않습니다.",
        )


def require_admin(current_user=Depends(get_current_user)):
    if current_user.role != "ADMIN":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="관리자 권한이 필요합니다.",
        )
    return current_user


def get_project_for_current_user(
    project_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    from app.models.project import Project, ProjectAccess

    project = db.get(Project, project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROJECT_NOT_FOUND_DETAIL)
    if current_user.role == "ADMIN":
        return project
    access = (
        db.query(ProjectAccess)
        .filter(
            ProjectAccess.project_id == project.id,
            ProjectAccess.user_id == current_user.id,
        )
        .first()
    )
    if not access:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=PROJECT_NOT_FOUND_DETAIL)
    return project


@lru_cache
def get_source_workspace() -> SourceWorkspace:
    return SourceWorkspace(Path(settings.STORAGE_ROOT).resolve())


@lru_cache
def get_upload_locks() -> ProjectUploadLocks:
    return ProjectUploadLocks()


@lru_cache
def get_analysis_executor():
    from app.services.analysis_executor import AnalysisExecutor

    return AnalysisExecutor()
