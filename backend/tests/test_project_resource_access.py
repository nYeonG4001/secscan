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


def login(client: TestClient, email: str) -> dict[str, str]:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    assert csrf_token
    return {"X-CSRF-Token": csrf_token}


@pytest.fixture
def project_data(db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    allowed_user = create_user(db_session, email="allowed@secscan.io", role="USER")
    denied_user = create_user(db_session, email="denied@secscan.io", role="USER")
    allowed_project = Project(name="허용 프로젝트", created_by=admin.id)
    other_project = Project(name="비허용 프로젝트", created_by=admin.id)
    empty_project = Project(name="분석 없는 허용 프로젝트", created_by=admin.id)
    db_session.add_all([allowed_project, other_project, empty_project])
    db_session.commit()
    db_session.refresh(allowed_project)
    db_session.refresh(other_project)
    db_session.refresh(empty_project)
    db_session.add_all(
        [
            ProjectAccess(
                project_id=allowed_project.id, user_id=allowed_user.id, granted_by=admin.id
            ),
            ProjectAccess(
                project_id=empty_project.id, user_id=allowed_user.id, granted_by=admin.id
            ),
        ]
    )
    allowed_analysis = Analysis(
        project_id=allowed_project.id,
        executed_by=admin.id,
        status="FAILED",
        engine="semgrep",
        error_code="ENGINE_ERROR",
        error_message="internal engine detail",
        source_snapshot_location="/private/snapshot/allowed",
    )
    other_analysis = Analysis(
        project_id=other_project.id,
        executed_by=admin.id,
        status="COMPLETED",
        source_snapshot_location="/private/snapshot/other",
    )
    db_session.add_all([allowed_analysis, other_analysis])
    db_session.commit()
    db_session.refresh(allowed_analysis)
    db_session.refresh(other_analysis)
    allowed_finding = Finding(
        analysis_id=allowed_analysis.id,
        file_path="allowed.py",
        raw_result={"internal": "allowed"},
    )
    other_finding = Finding(
        analysis_id=other_analysis.id,
        file_path="other.py",
        raw_result={"internal": "other"},
    )
    db_session.add_all([allowed_finding, other_finding])
    db_session.commit()
    db_session.refresh(allowed_finding)
    db_session.refresh(other_finding)
    return {
        "admin": admin,
        "allowed_user": allowed_user,
        "denied_user": denied_user,
        "allowed_project": allowed_project,
        "other_project": other_project,
        "empty_project": empty_project,
        "allowed_analysis": allowed_analysis,
        "other_analysis": other_analysis,
        "allowed_finding": allowed_finding,
        "other_finding": other_finding,
    }


def test_admin_lists_and_reads_every_project_resource(client, project_data):
    login(client, project_data["admin"].email)

    assert len(client.get("/projects/").json()) == 3
    assert client.get(f"/projects/{project_data['other_project'].id}").status_code == 200
    assert client.get(
        "/analyses/", params={"project_id": project_data["other_project"].id}
    ).status_code == 200
    assert client.get(f"/analyses/{project_data['other_analysis'].id}").status_code == 200
    assert client.get(
        "/findings/", params={"analysis_id": project_data["other_analysis"].id}
    ).status_code == 200
    assert client.get(f"/findings/{project_data['other_finding'].id}").status_code == 200


def test_user_only_reads_currently_granted_project_resources_and_not_ids(client, project_data):
    login(client, project_data["allowed_user"].email)

    listed_ids = {project["id"] for project in client.get("/projects/").json()}
    assert listed_ids == {project_data["allowed_project"].id, project_data["empty_project"].id}
    assert client.get(f"/projects/{project_data['allowed_project'].id}").status_code == 200
    assert client.get(f"/projects/{project_data['empty_project'].id}").status_code == 200
    assert client.get(
        "/analyses/", params={"project_id": project_data["allowed_project"].id}
    ).status_code == 200
    assert client.get(f"/analyses/{project_data['allowed_analysis'].id}").status_code == 200
    assert client.get(
        "/findings/", params={"analysis_id": project_data["allowed_analysis"].id}
    ).status_code == 200
    assert client.get(f"/findings/{project_data['allowed_finding'].id}").status_code == 200

    assert client.get(f"/projects/{project_data['other_project'].id}").status_code == 404
    assert client.get(
        "/analyses/", params={"project_id": project_data["other_project"].id}
    ).status_code == 404
    assert client.get(f"/analyses/{project_data['other_analysis'].id}").status_code == 404
    assert client.get(
        "/findings/", params={"analysis_id": project_data["other_analysis"].id}
    ).status_code == 404
    assert client.get(f"/findings/{project_data['other_finding'].id}").status_code == 404


def test_access_grant_and_revoke_take_effect_immediately_for_detail_and_list(client, project_data):
    target_project = project_data["other_project"]
    user = project_data["denied_user"]

    login(client, user.email)
    assert client.get(f"/projects/{target_project.id}").status_code == 404

    admin_headers = login(client, project_data["admin"].email)
    assert client.post(
        f"/projects/{target_project.id}/access", json={"email": user.email}, headers=admin_headers
    ).status_code == 200

    login(client, user.email)
    assert client.get(f"/projects/{target_project.id}").status_code == 200
    assert target_project.id in {project["id"] for project in client.get("/projects/").json()}

    admin_headers = login(client, project_data["admin"].email)
    assert client.delete(
        f"/projects/{target_project.id}/access/{user.id}", headers=admin_headers
    ).status_code == 204

    login(client, user.email)
    assert client.get(f"/projects/{target_project.id}").status_code == 404
    assert target_project.id not in {project["id"] for project in client.get("/projects/").json()}
    assert client.get(
        "/analyses/", params={"project_id": target_project.id}
    ).status_code == 404
    assert client.get(f"/analyses/{project_data['other_analysis'].id}").status_code == 404
    assert client.get(
        "/findings/", params={"analysis_id": project_data["other_analysis"].id}
    ).status_code == 404
    assert client.get(f"/findings/{project_data['other_finding'].id}").status_code == 404


def test_missing_project_analysis_and_finding_all_return_404(client, project_data):
    login(client, project_data["allowed_user"].email)

    assert client.get("/projects/9999").status_code == 404
    assert client.get("/analyses/", params={"project_id": 9999}).status_code == 404
    assert client.get("/analyses/9999").status_code == 404
    assert client.get("/findings/", params={"analysis_id": 9999}).status_code == 404
    assert client.get("/findings/9999").status_code == 404


def test_allowed_user_response_keeps_sensitive_fields_hidden_after_access_check(
    client, project_data
):
    login(client, project_data["allowed_user"].email)

    analysis_response = client.get(f"/analyses/{project_data['allowed_analysis'].id}")
    finding_response = client.get(f"/findings/{project_data['allowed_finding'].id}")
    assert analysis_response.status_code == 200
    assert finding_response.status_code == 200
    assert {"engine", "error_code", "error_message", "source_snapshot_location"}.isdisjoint(
        analysis_response.json()
    )
    assert "raw_result" not in finding_response.json()

    login(client, project_data["admin"].email)
    admin_analysis = client.get(f"/analyses/{project_data['allowed_analysis'].id}").json()
    admin_finding = client.get(f"/findings/{project_data['allowed_finding'].id}").json()
    assert {"engine", "error_code", "error_message"} <= set(admin_analysis)
    assert "source_snapshot_location" not in admin_analysis
    assert admin_finding["raw_result"] == {"internal": "allowed"}
