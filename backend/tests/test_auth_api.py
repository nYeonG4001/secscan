from datetime import timedelta
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import (
    DUMMY_PASSWORD_HASH,
    create_access_token,
    hash_password,
)
from app.main import app
from app.models.user import User


@pytest.fixture
def client(db_session: Session):
    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def create_user(
    db_session: Session,
    *,
    email: str,
    role: str,
    active: bool = True,
    password: str = "correct-password",
) -> User:
    user = User(
        email=email,
        password_hash=hash_password(password),
        role=role,
        active=active,
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.mark.parametrize("role", ["ADMIN", "USER"])
def test_active_account_can_log_in(client, db_session, role):
    email = f"{role.lower()}@secscan.io"
    create_user(db_session, email=email, role=role)

    response = client.post("/auth/login", json={"email": email, "password": "correct-password"})

    assert response.status_code == 200
    assert response.json() == {"email": email, "role": role}
    assert client.cookies.get(settings.SESSION_COOKIE_NAME)
    assert client.cookies.get(settings.CSRF_COOKIE_NAME)


def test_login_rejects_invalid_email_format(client):
    response = client.post(
        "/auth/login", json={"email": "not-an-email", "password": "correct-password"}
    )

    assert response.status_code == 422


def test_inactive_account_login_is_rejected_without_state_disclosure(client, db_session):
    create_user(
        db_session,
        email="inactive@secscan.io",
        role="USER",
        active=False,
    )

    response = client.post(
        "/auth/login",
        json={"email": "inactive@secscan.io", "password": "correct-password"},
    )

    assert response.status_code == 401
    assert "활성" not in response.json()["detail"]


@pytest.mark.parametrize(
    ("email", "password"),
    [
        ("missing@secscan.io", "correct-password"),
        ("user@secscan.io", "wrong-password"),
    ],
)
def test_unknown_user_and_wrong_password_return_generic_401(client, db_session, email, password):
    create_user(db_session, email="user@secscan.io", role="USER")

    response = client.post("/auth/login", json={"email": email, "password": password})

    assert response.status_code == 401
    assert response.json()["detail"] == "이메일 또는 비밀번호가 올바르지 않습니다."


def test_login_response_does_not_expose_authentication_secrets(client, db_session):
    create_user(db_session, email="user@secscan.io", role="USER")

    response = client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )

    assert response.status_code == 200
    assert set(response.json()) == {"email", "role"}
    assert not {
        "access_token",
        "token_type",
        "password",
        "password_hash",
        "active",
    } & set(response.json())


def test_login_sets_httponly_session_cookie_and_readable_csrf_cookie(client, db_session):
    create_user(db_session, email="user@secscan.io", role="USER")

    response = client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )

    set_cookie_headers = response.headers.get_list("set-cookie")
    session_cookie = next(
        header
        for header in set_cookie_headers
        if header.startswith(f"{settings.SESSION_COOKIE_NAME}=")
    )
    csrf_cookie = next(
        header
        for header in set_cookie_headers
        if header.startswith(f"{settings.CSRF_COOKIE_NAME}=")
    )
    assert "HttpOnly" in session_cookie
    assert "HttpOnly" not in csrf_cookie
    assert "SameSite=strict" in session_cookie
    assert "Path=/" in session_cookie
    assert "Max-Age=86400" in session_cookie


def test_session_cookie_secure_setting_changes_by_environment(client, db_session, monkeypatch):
    create_user(db_session, email="user@secscan.io", role="USER")
    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", False)
    insecure_response = client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )
    assert "Secure" not in insecure_response.headers.get_list("set-cookie")[0]

    monkeypatch.setattr(settings, "SESSION_COOKIE_SECURE", True)
    secure_response = client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )
    assert "Secure" in secure_response.headers.get_list("set-cookie")[0]


def test_missing_user_login_still_runs_password_verification(client, db_session):
    with patch(
        "app.routers.auth.verify_password", wraps=lambda *_args, **_kwargs: False
    ) as spied_verify:
        response = client.post(
            "/auth/login",
            json={"email": "missing@secscan.io", "password": "irrelevant-password"},
        )

    assert response.status_code == 401
    spied_verify.assert_called_once_with("irrelevant-password", DUMMY_PASSWORD_HASH)


def test_inactive_user_login_still_runs_password_verification(client, db_session):
    create_user(db_session, email="inactive@secscan.io", role="USER", active=False)

    with patch(
        "app.routers.auth.verify_password", wraps=lambda *_args, **_kwargs: True
    ) as spied_verify:
        response = client.post(
            "/auth/login",
            json={"email": "inactive@secscan.io", "password": "correct-password"},
        )

    assert response.status_code == 401
    spied_verify.assert_called_once()
    called_password_hash = spied_verify.call_args.args[1]
    assert called_password_hash != DUMMY_PASSWORD_HASH


def test_existing_token_is_rejected_after_account_is_deactivated(client, db_session):
    user = create_user(db_session, email="user@secscan.io", role="USER")
    client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )
    user.active = False
    db_session.commit()

    response = client.get("/projects/")

    assert response.status_code == 401
    assert response.json()["detail"] == "인증 정보가 유효하지 않습니다."


@pytest.mark.parametrize(
    "token",
    [
        create_access_token({"sub": "not-an-id"}),
        create_access_token({"sub": "1"}, expires_delta=timedelta(seconds=-1)),
        "tampered.session.token",
    ],
)
def test_invalid_session_cookie_is_rejected(client, db_session, token):
    create_user(db_session, email="user@secscan.io", role="USER")
    client.cookies.set(settings.SESSION_COOKIE_NAME, token)

    response = client.get("/projects/")

    assert response.status_code == 401
    assert response.json()["detail"] == "인증 정보가 유효하지 않습니다."


def test_missing_session_cookie_is_rejected(client):
    response = client.get("/projects/")

    assert response.status_code == 401


def test_auth_me_returns_only_email_and_role(client, db_session):
    create_user(db_session, email="user@secscan.io", role="USER")
    client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )

    response = client.get("/auth/me")

    assert response.status_code == 200
    assert response.json() == {"email": "user@secscan.io", "role": "USER"}


def test_logout_is_idempotent_and_clears_authentication_cookies(client, db_session):
    create_user(db_session, email="user@secscan.io", role="USER")
    client.post(
        "/auth/login",
        json={"email": "user@secscan.io", "password": "correct-password"},
    )

    response = client.post("/auth/logout")

    assert response.status_code == 204
    cleared_cookie_headers = response.headers.get_list("set-cookie")
    assert all("Max-Age=0" in header for header in cleared_cookie_headers)
    assert client.get("/projects/").status_code == 401
    assert client.post("/auth/logout").status_code == 204
