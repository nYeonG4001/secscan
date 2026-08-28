import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.project import Project, ProjectAccess
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


def create_project(db_session: Session, *, name: str, created_by: int) -> Project:
    project = Project(name=name, created_by=created_by)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    assert csrf_token
    return {"X-CSRF-Token": csrf_token}


def test_admin_grants_access_by_user_email_and_lists_both_user_identifiers(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="권한 부여 대상", created_by=admin.id)
    headers = login(client, admin.email)

    granted = client.post(
        f"/projects/{project.id}/access", json={"email": member.email}, headers=headers
    )

    assert granted.status_code == 200
    assert granted.json()["user_id"] == member.id
    assert granted.json()["user_email"] == member.email
    listed = client.get(f"/projects/{project.id}/access")
    assert listed.status_code == 200
    assert listed.json()[0]["user_id"] == member.id
    assert listed.json()[0]["user_email"] == member.email


def test_access_grant_rejects_missing_target_admin_target_and_duplicate(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    other_admin = create_user(db_session, email="other-admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="권한 부여 거부 대상", created_by=admin.id)
    headers = login(client, admin.email)

    assert client.post(
        f"/projects/{project.id}/access", json={"email": "missing@secscan.io"}, headers=headers
    ).status_code == 404
    assert client.post(
        f"/projects/{project.id}/access", json={"email": other_admin.email}, headers=headers
    ).status_code == 422
    assert client.post(
        f"/projects/{project.id}/access", json={"email": member.email}, headers=headers
    ).status_code == 200
    assert client.post(
        f"/projects/{project.id}/access", json={"email": member.email}, headers=headers
    ).status_code == 409


def test_access_routes_return_404_for_missing_project(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    headers = login(client, admin.email)

    assert client.get("/projects/9999/access").status_code == 404
    assert client.post(
        "/projects/9999/access", json={"email": member.email}, headers=headers
    ).status_code == 404
    assert client.delete("/projects/9999/access/9999", headers=headers).status_code == 404


def test_admin_revokes_only_access_relationship_and_user_delete_is_forbidden(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="권한 해제 대상", created_by=admin.id)
    access = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    analysis = Analysis(project_id=project.id, executed_by=admin.id, status="COMPLETED")
    db_session.add_all([access, analysis])
    db_session.commit()
    access_id = access.id
    db_session.refresh(analysis)
    finding = Finding(analysis_id=analysis.id, file_path="src/App.java", message="보존 확인")
    db_session.add(finding)
    db_session.commit()

    member_headers = login(client, member.email)
    assert client.delete(
        f"/projects/{project.id}/access/{member.id}", headers=member_headers
    ).status_code == 403

    admin_headers = login(client, admin.email)
    assert client.delete(
        f"/projects/{project.id}/access/{member.id}", headers=admin_headers
    ).status_code == 204
    assert client.delete(
        f"/projects/{project.id}/access/{member.id}", headers=admin_headers
    ).status_code == 404
    assert db_session.get(Project, project.id)
    assert db_session.get(Analysis, analysis.id)
    assert db_session.get(Finding, finding.id)
    assert not db_session.get(ProjectAccess, access_id)


def test_unauthenticated_access_revocation_returns_401(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="미인증 해제 대상", created_by=admin.id)
    access = ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id)
    db_session.add(access)
    db_session.commit()

    assert client.delete(f"/projects/{project.id}/access/{member.id}").status_code == 401
