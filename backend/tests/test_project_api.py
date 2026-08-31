import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.project import Project
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


def create_user(db_session: Session, *, email: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password("correct-password"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def login(client, email: str) -> str:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return client.cookies.get("secscan_csrf")


def auth_headers(token: str) -> dict:
    return {"X-CSRF-Token": token}


def test_admin_can_create_project_with_only_name_and_description(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/projects/",
        json={"name": "보안 교육 샘플", "description": "샘플 프로젝트"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "보안 교육 샘플"
    assert body["description"] == "샘플 프로젝트"
    assert body["created_by"] == admin.id
    assert body["source_type"] is None
    assert body["target_languages"] is None
    assert "source_location" not in body
    assert body["created_at"] is not None
    assert body["updated_at"] is not None


def test_project_description_is_optional(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/projects/", json={"name": "설명 없는 프로젝트"}, headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["description"] is None


def test_project_list_exposes_computed_source_and_latest_analysis_status(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    project = Project(
        name="분석 상태 프로젝트",
        created_by=admin.id,
        source_location="/internal/current-source",
        target_languages=["JAVA", "PYTHON"],
    )
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    db_session.add_all(
        [
            Analysis(project_id=project.id, executed_by=admin.id, status="FAILED"),
            Analysis(project_id=project.id, executed_by=admin.id, status="COMPLETED"),
        ]
    )
    db_session.commit()

    login(client, admin.email)
    response = client.get("/projects/")

    assert response.status_code == 200
    body = response.json()[0]
    assert body["source_status"] == "REGISTERED"
    assert body["latest_analysis_status"] == "COMPLETED"
    assert body["target_languages"] == ["JAVA", "PYTHON"]


def test_create_project_missing_name_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/projects/", json={"description": "이름이 없음"}, headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_create_project_rejects_blank_name(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post("/projects/", json={"name": ""}, headers=auth_headers(token))

    assert response.status_code == 422


def test_create_project_request_does_not_accept_target_languages(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/projects/",
        json={"name": "언어 지정 시도", "target_languages": ["JAVA"]},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["target_languages"] is None


def test_non_admin_cannot_create_project(client, db_session):
    create_user(db_session, email="admin@secscan.io", role="ADMIN")
    user = create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, user.email)

    response = client.post(
        "/projects/", json={"name": "일반 사용자 시도"}, headers=auth_headers(token)
    )

    assert response.status_code == 403


def test_write_requests_require_a_matching_csrf_header(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    csrf_token = login(client, admin.email)

    missing = client.post("/projects/", json={"name": "CSRF 누락"})
    invalid = client.post(
        "/projects/",
        json={"name": "CSRF 불일치"},
        headers={"X-CSRF-Token": "incorrect"},
    )
    valid = client.post(
        "/projects/",
        json={"name": "CSRF 일치"},
        headers=auth_headers(csrf_token),
    )

    assert missing.status_code == 403
    assert invalid.status_code == 403
    assert valid.status_code == 200


def test_duplicate_project_name_gets_auto_numbered(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    first = client.post(
        "/projects/", json={"name": "보안 교육 샘플"}, headers=auth_headers(token)
    )
    second = client.post(
        "/projects/", json={"name": "보안 교육 샘플"}, headers=auth_headers(token)
    )
    third = client.post(
        "/projects/", json={"name": "보안 교육 샘플"}, headers=auth_headers(token)
    )

    assert first.json()["name"] == "보안 교육 샘플"
    assert second.json()["name"] == "보안 교육 샘플 (1)"
    assert third.json()["name"] == "보안 교육 샘플 (2)"
    assert first.json()["id"] != second.json()["id"] != third.json()["id"]


def test_admin_can_update_project_name_and_description(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    created = client.post(
        "/projects/", json={"name": "원래 이름"}, headers=auth_headers(token)
    ).json()

    response = client.patch(
        f"/projects/{created['id']}",
        json={"name": "새 이름", "description": "새 설명"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "새 이름"
    assert body["description"] == "새 설명"


def test_update_does_not_change_creator_or_created_at(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    created = client.post(
        "/projects/", json={"name": "원래 이름"}, headers=auth_headers(token)
    ).json()

    response = client.patch(
        f"/projects/{created['id']}",
        json={"description": "설명만 수정"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert body["created_by"] == created["created_by"]
    assert body["created_at"] == created["created_at"]


def test_update_to_duplicate_name_gets_auto_numbered(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    client.post("/projects/", json={"name": "고정 이름"}, headers=auth_headers(token))
    other = client.post(
        "/projects/", json={"name": "다른 이름"}, headers=auth_headers(token)
    ).json()

    response = client.patch(
        f"/projects/{other['id']}",
        json={"name": "고정 이름"},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    assert response.json()["name"] == "고정 이름 (1)"


def test_update_missing_project_returns_404(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.patch(
        "/projects/9999", json={"name": "없는 프로젝트"}, headers=auth_headers(token)
    )

    assert response.status_code == 404


def test_delete_project_route_is_removed(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    created = client.post(
        "/projects/", json={"name": "삭제 시도 대상"}, headers=auth_headers(token)
    ).json()

    response = client.delete(f"/projects/{created['id']}", headers=auth_headers(token))

    assert response.status_code in (404, 405)
