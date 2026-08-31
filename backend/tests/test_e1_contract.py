"""E1-09: final consolidated audit for the E1 data-model epic.

Each E1-0X task already verified its own slice of the model/schema/API
surface (see test_user_model.py, test_project_api.py,
test_project_access_model.py, test_analysis_schema.py,
test_finding_schema.py, test_catalog_schema.py, test_api_contract.py,
test_migrations.py). This file does not repeat that coverage. It adds the
two things none of those files owned end to end:

1. A required-field sweep across all six entities (User, Project,
   ProjectAccess, Analysis, Finding, KisaCatalog) — missing a NOT NULL
   field with no default raises IntegrityError at the model level, or 422
   at the API level where a request schema exists. Prior coverage of this
   was scattered across files and incomplete for some entities
   (ProjectAccess, Analysis, Finding had no missing-required-field test at
   all before this file).
2. One end-to-end integration test that drives the real FastAPI app
   through the actual user-facing flow (login -> project -> access grant
   -> analysis -> catalog) and checks every field the API returns against
   docs/erd.md and docs/api-contract.md.
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
from app.models.project import Project, ProjectAccess
from app.models.user import User
from app.services.kisa_catalog_seed import seed_kisa_catalog

# ---------------------------------------------------------------------------
# Shared fixtures/helpers (same pattern as the other API test files)
# ---------------------------------------------------------------------------


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


def create_user(db_session, *, email: str, role: str) -> User:
    user = User(email=email, password_hash=hash_password("correct-password"), role=role)
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


def create_project(db_session, *, name: str, created_by: int) -> Project:
    project = Project(name=name, created_by=created_by)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)
    return project


def login(client, email: str) -> str:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return client.cookies.get("secscan_csrf")


def auth_headers(token: str) -> dict:
    return {"X-CSRF-Token": token}


# ---------------------------------------------------------------------------
# 1. Required-field sweep — model level (IntegrityError)
# ---------------------------------------------------------------------------


def test_user_missing_email_is_rejected(db_session):
    db_session.add(User(password_hash=hash_password("password")))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_user_missing_password_hash_is_rejected(db_session):
    db_session.add(User(email="nopass@secscan.io"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_missing_created_by_is_rejected(db_session):
    # Not reachable through POST /projects (the router always fills
    # created_by from the authenticated admin), so this can only be
    # exercised by constructing the model directly.
    db_session.add(Project(name="생성자 없는 프로젝트"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_access_missing_project_id_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    db_session.add(ProjectAccess(user_id=admin.id, granted_by=admin.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_access_missing_user_id_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    project = create_project(db_session, name="접근권한 필수값 테스트", created_by=admin.id)
    db_session.add(ProjectAccess(project_id=project.id, granted_by=admin.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_project_access_missing_granted_by_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="접근권한 필수값 테스트2", created_by=admin.id)
    db_session.add(ProjectAccess(project_id=project.id, user_id=member.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_analysis_missing_project_id_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    db_session.add(Analysis(executed_by=admin.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_analysis_missing_executed_by_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    project = create_project(db_session, name="분석 필수값 테스트", created_by=admin.id)
    db_session.add(Analysis(project_id=project.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_finding_missing_analysis_id_is_rejected(db_session):
    db_session.add(Finding(file_path="src/App.java"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_finding_missing_file_path_is_rejected(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    project = create_project(db_session, name="결과 필수값 테스트", created_by=admin.id)
    analysis = Analysis(project_id=project.id, executed_by=admin.id, status="COMPLETED")
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    db_session.add(Finding(analysis_id=analysis.id))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_kisa_catalog_missing_category_is_rejected(db_session):
    db_session.add(KisaCatalog(kisa_code="SWEEP-001", name="테스트 항목", default_severity="LOW"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_kisa_catalog_missing_name_is_rejected(db_session):
    db_session.add(
        KisaCatalog(kisa_code="SWEEP-002", category="보안기능", default_severity="LOW")
    )
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


def test_kisa_catalog_missing_default_severity_is_rejected(db_session):
    db_session.add(KisaCatalog(kisa_code="SWEEP-003", category="보안기능", name="테스트 항목"))
    with pytest.raises(IntegrityError):
        db_session.commit()
    db_session.rollback()


# ---------------------------------------------------------------------------
# 1. Required-field sweep — API level (422)
# ---------------------------------------------------------------------------


def test_login_missing_email_returns_422(client):
    response = client.post("/auth/login", json={"password": "correct-password"})
    assert response.status_code == 422


def test_login_missing_password_returns_422(client):
    response = client.post("/auth/login", json={"email": "user@secscan.io"})
    assert response.status_code == 422


def test_grant_access_missing_email_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)
    project = create_project(db_session, name="접근권한 API 필수값 테스트", created_by=admin.id)

    response = client.post(
        f"/projects/{project.id}/access", json={}, headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_create_analysis_missing_project_id_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/analyses/",
        json={},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_create_analysis_missing_body_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/analyses/", json={}, headers=auth_headers(token)
    )

    assert response.status_code == 422


def test_register_catalog_item_missing_name_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/catalog/",
        json={"kisa_code": "SWEEP-API-001", "category": "보안기능", "default_severity": "LOW"},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_register_catalog_item_missing_category_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/catalog/",
        json={"kisa_code": "SWEEP-API-002", "name": "테스트 항목", "default_severity": "LOW"},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


def test_register_catalog_item_missing_default_severity_returns_422(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    token = login(client, admin.email)

    response = client.post(
        "/catalog/",
        json={"kisa_code": "SWEEP-API-003", "name": "테스트 항목", "category": "보안기능"},
        headers=auth_headers(token),
    )

    assert response.status_code == 422


# ---------------------------------------------------------------------------
# 2. Post-migration end-to-end contract check
# ---------------------------------------------------------------------------

# Field sets per docs/api-contract.md / docs/erd.md / ADR-009, restated
# here as the audit's ground truth so a future accidental field
# addition/removal in a schema fails this test rather than going unnoticed.
PROJECT_FIELDS = {
    "id",
    "name",
    "description",
    "source_type",
    "source_status",
    "latest_analysis_status",
    "target_languages",
    "created_by",
    "created_at",
    "updated_at",
}
PROJECT_ACCESS_FIELDS = {"id", "project_id", "user_id", "user_email", "granted_at", "granted_by"}
ANALYSIS_USER_FIELDS = {
    "id",
    "project_id",
    "executed_by",
    "status",
    "created_at",
    "started_at",
    "completed_at",
    "summary",
}
ANALYSIS_ADMIN_ONLY_FIELDS = {
    "engine",
    "analyzed_languages",
    "error_code",
    "error_message",
    "execution_log",
}
CATALOG_ITEM_FIELDS = {
    "kisa_code",
    "criterion_id",
    "item_number",
    "category",
    "name",
    "description",
    "reference_info",
    "default_severity",
    "active",
    "implementation_status",
    "recommendation",
}


def test_end_to_end_flow_matches_documented_api_contract(client, db_session):
    # -- seed and log in as ADMIN --
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    seed_kisa_catalog(db_session)
    admin_token = login(client, admin.email)

    # -- create a project --
    project_response = client.post(
        "/projects/",
        json={"name": "E1-09 통합 테스트 프로젝트", "description": "엔드투엔드 검증용"},
        headers=auth_headers(admin_token),
    )
    assert project_response.status_code == 200
    project_body = project_response.json()
    assert set(project_body) == PROJECT_FIELDS
    project_id = project_body["id"]

    # -- grant the USER access to the project --
    access_response = client.post(
        f"/projects/{project_id}/access",
        json={"email": member.email},
        headers=auth_headers(admin_token),
    )
    assert access_response.status_code == 200
    assert set(access_response.json()) == PROJECT_ACCESS_FIELDS

    # -- create an analysis from E3's already registered source --
    project = db_session.get(Project, project_id)
    project.source_location = "projects/1/sources/0123456789abcdef0123456789abcdef"
    project.target_languages = ["JAVA"]
    db_session.commit()
    analysis_response = client.post(
        "/analyses/",
        json={"project_id": project_id},
        headers=auth_headers(admin_token),
    )
    assert analysis_response.status_code == 201
    analysis_id = analysis_response.json()["id"]

    # Populate admin-only fields directly (E4's execution pipeline isn't built
    # yet) so the role-based field split below has something to prove.
    analysis = db_session.get(Analysis, analysis_id)
    analysis.engine = "semgrep"
    analysis.analyzed_languages = ["JAVA"]
    analysis.source_snapshot_location = "/var/secscan/snapshots/e1-09"
    analysis.status = "FAILED"
    analysis.error_code = "ENGINE_ERROR"
    analysis.error_message = "semgrep exited with code 1"
    analysis.execution_log = "engine diagnostic"
    db_session.commit()

    finding = Finding(
        analysis_id=analysis_id,
        kisa_code="KISA-001",
        criterion_id="4.1.1",
        file_path="src/main/java/App.java",
        message="탐지된 문제",
        raw_result={"tool": "semgrep"},
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    # -- fetch the analysis as ADMIN: admin-only fields present, snapshot location never exposed --
    admin_analysis = client.get(
        f"/analyses/{analysis_id}", headers=auth_headers(admin_token)
    ).json()
    assert ANALYSIS_USER_FIELDS <= set(admin_analysis)
    assert ANALYSIS_ADMIN_ONLY_FIELDS <= set(admin_analysis)
    assert "source_snapshot_location" not in admin_analysis
    assert "raw_result" not in admin_analysis

    # -- fetch the analysis as USER: admin-only fields absent --
    member_token = login(client, member.email)
    user_analysis = client.get(
        f"/analyses/{analysis_id}", headers=auth_headers(member_token)
    ).json()
    assert set(user_analysis) == ANALYSIS_USER_FIELDS
    assert user_analysis["status"] == "FAILED"

    # -- catalog: same field set for both roles, 49 seeded items reachable --
    admin_catalog = client.get("/catalog/", headers=auth_headers(admin_token)).json()
    user_catalog = client.get("/catalog/", headers=auth_headers(member_token)).json()
    assert len(admin_catalog) == 49
    assert len(user_catalog) == 49
    assert set(admin_catalog[0]) == CATALOG_ITEM_FIELDS
    assert set(user_catalog[0]) == CATALOG_ITEM_FIELDS
