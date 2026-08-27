import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.project import Project
from app.models.user import User

ADMIN_ONLY_ANALYSIS_FIELDS = {"engine", "analyzed_languages", "error_code", "error_message"}


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


def login(client, email: str) -> str:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


def auth_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def seeded_analysis(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    project = Project(name="계약 테스트 프로젝트", created_by=admin.id)
    db_session.add(project)
    db_session.commit()
    db_session.refresh(project)

    analysis = Analysis(
        project_id=project.id,
        executed_by=admin.id,
        engine="semgrep",
        analyzed_languages=["JAVA"],
        source_snapshot_location="/var/secscan/snapshots/1",
        status="FAILED",
        error_code="ENGINE_ERROR",
        error_message="semgrep exited with code 1",
        summary={"total_findings": 1},
    )
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)

    finding = Finding(
        analysis_id=analysis.id,
        file_path="src/main/java/App.java",
        message="탐지된 문제",
        raw_result={"tool": "semgrep", "check_id": "java.sql-injection"},
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    return {"admin": admin, "project": project, "analysis": analysis, "finding": finding}


def test_user_analysis_list_excludes_admin_only_and_snapshot_fields(
    client, db_session, seeded_analysis
):
    create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, "user@secscan.io")

    response = client.get(
        "/analyses/",
        params={"project_id": seeded_analysis["project"].id},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    exposed = set(body[0])
    assert exposed.isdisjoint(ADMIN_ONLY_ANALYSIS_FIELDS)
    assert "source_snapshot_location" not in exposed
    assert body[0]["status"] == "FAILED"
    assert body[0]["summary"] == {"total_findings": 1}


def test_admin_analysis_list_includes_admin_only_fields(client, db_session, seeded_analysis):
    token = login(client, seeded_analysis["admin"].email)

    response = client.get(
        "/analyses/",
        params={"project_id": seeded_analysis["project"].id},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()[0]
    assert ADMIN_ONLY_ANALYSIS_FIELDS <= set(body)
    assert body["engine"] == "semgrep"
    assert body["error_code"] == "ENGINE_ERROR"
    assert body["error_message"] == "semgrep exited with code 1"
    assert "source_snapshot_location" not in body


def test_user_analysis_detail_excludes_admin_only_and_snapshot_fields(
    client, db_session, seeded_analysis
):
    create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, "user@secscan.io")

    response = client.get(
        f"/analyses/{seeded_analysis['analysis'].id}", headers=auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body).isdisjoint(ADMIN_ONLY_ANALYSIS_FIELDS)
    assert "source_snapshot_location" not in body


def test_admin_analysis_detail_includes_admin_only_fields(client, db_session, seeded_analysis):
    token = login(client, seeded_analysis["admin"].email)

    response = client.get(
        f"/analyses/{seeded_analysis['analysis'].id}", headers=auth_headers(token)
    )

    assert response.status_code == 200
    body = response.json()
    assert ADMIN_ONLY_ANALYSIS_FIELDS <= set(body)
    assert "source_snapshot_location" not in body


def test_user_finding_list_excludes_raw_result(client, db_session, seeded_analysis):
    create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, "user@secscan.io")

    response = client.get(
        "/findings/",
        params={"analysis_id": seeded_analysis["analysis"].id},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert "raw_result" not in body[0]


def test_admin_finding_list_includes_raw_result(client, db_session, seeded_analysis):
    token = login(client, seeded_analysis["admin"].email)

    response = client.get(
        "/findings/",
        params={"analysis_id": seeded_analysis["analysis"].id},
        headers=auth_headers(token),
    )

    assert response.status_code == 200
    body = response.json()[0]
    assert body["raw_result"] == {"tool": "semgrep", "check_id": "java.sql-injection"}


def test_user_finding_detail_excludes_raw_result(client, db_session, seeded_analysis):
    create_user(db_session, email="user@secscan.io", role="USER")
    token = login(client, "user@secscan.io")

    response = client.get(
        f"/findings/{seeded_analysis['finding'].id}", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert "raw_result" not in response.json()


def test_admin_finding_detail_includes_raw_result(client, db_session, seeded_analysis):
    token = login(client, seeded_analysis["admin"].email)

    response = client.get(
        f"/findings/{seeded_analysis['finding'].id}", headers=auth_headers(token)
    )

    assert response.status_code == 200
    assert response.json()["raw_result"] == {"tool": "semgrep", "check_id": "java.sql-injection"}


def test_openapi_schema_is_generated(client):
    response = client.get("/openapi.json")

    assert response.status_code == 200
    schema = response.json()
    assert "/analyses/" in schema["paths"]
    assert "/findings/" in schema["paths"]
