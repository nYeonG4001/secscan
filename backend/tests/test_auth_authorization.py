import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import SessionLocal, get_db
from app.core.security import create_access_token, hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
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


def login(client: TestClient, email: str) -> str:
    response = client.post(
        "/auth/login", json={"email": email, "password": "correct-password"}
    )
    assert response.status_code == 200
    csrf_token = client.cookies.get(settings.CSRF_COOKIE_NAME)
    assert csrf_token
    return csrf_token


def csrf_headers(csrf_token: str) -> dict[str, str]:
    return {"X-CSRF-Token": csrf_token}


def test_admin_can_call_every_current_admin_api_with_valid_csrf(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    csrf_token = login(client, admin.email)
    headers = csrf_headers(csrf_token)

    created_project = client.post(
        "/projects/", json={"name": "관리자 권한 테스트"}, headers=headers
    )
    assert created_project.status_code == 200
    project_id = created_project.json()["id"]

    assert client.patch(
        f"/projects/{project_id}", json={"description": "수정됨"}, headers=headers
    ).status_code == 200
    assert client.get(f"/projects/{project_id}/access").status_code == 200
    assert client.post(
        f"/projects/{project_id}/access", json={"email": member.email}, headers=headers
    ).status_code == 200
    assert client.post(
        "/analyses/",
        data={"project_id": str(project_id)},
        files={"file": ("source.zip", b"source", "application/zip")},
        headers=headers,
    ).status_code == 200

    catalog_payload = {
        "kisa_code": "ROLE-001",
        "name": "역할 권한 테스트 항목",
        "category": "보안기능",
        "default_severity": "LOW",
    }
    assert client.post("/catalog/", json=catalog_payload, headers=headers).status_code == 201
    assert client.patch(
        "/catalog/ROLE-001", json={"description": "수정됨"}, headers=headers
    ).status_code == 200


def test_user_is_forbidden_from_every_current_admin_api_with_valid_csrf(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="관리자 전용 대상", created_by=admin.id)
    catalog = KisaCatalog(
        kisa_code="ROLE-002",
        category="보안기능",
        name="수정 대상",
        default_severity="LOW",
    )
    db_session.add(catalog)
    db_session.commit()
    headers = csrf_headers(login(client, member.email))

    responses = [
        client.post("/projects/", json={"name": "USER 생성 시도"}, headers=headers),
        client.patch(
            f"/projects/{project.id}", json={"description": "USER 수정 시도"}, headers=headers
        ),
        client.get(f"/projects/{project.id}/access"),
        client.post(
            f"/projects/{project.id}/access", json={"email": member.email}, headers=headers
        ),
        client.post(
            "/analyses/",
            data={"project_id": str(project.id)},
            files={"file": ("source.zip", b"source", "application/zip")},
            headers=headers,
        ),
        client.post(
            "/catalog/",
            json={
                "kisa_code": "ROLE-003",
                "name": "USER 등록 시도",
                "category": "보안기능",
                "default_severity": "LOW",
            },
            headers=headers,
        ),
        client.patch(
            "/catalog/ROLE-002", json={"description": "USER 수정 시도"}, headers=headers
        ),
    ]

    assert [response.status_code for response in responses] == [403] * len(responses)


def test_unauthenticated_requests_to_every_current_admin_api_return_401(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="미인증 대상", created_by=admin.id)
    catalog = KisaCatalog(
        kisa_code="ROLE-004",
        category="보안기능",
        name="미인증 수정 대상",
        default_severity="LOW",
    )
    db_session.add(catalog)
    db_session.commit()

    responses = [
        client.post("/projects/", json={"name": "미인증 생성 시도"}),
        client.patch(f"/projects/{project.id}", json={"description": "미인증 수정 시도"}),
        client.get(f"/projects/{project.id}/access"),
        client.post(f"/projects/{project.id}/access", json={"email": member.email}),
        client.post(
            "/analyses/",
            data={"project_id": str(project.id)},
            files={"file": ("source.zip", b"source", "application/zip")},
        ),
        client.post(
            "/catalog/",
            json={
                "kisa_code": "ROLE-005",
                "name": "미인증 등록 시도",
                "category": "보안기능",
                "default_severity": "LOW",
            },
        ),
        client.patch("/catalog/ROLE-004", json={"description": "미인증 수정 시도"}),
    ]

    assert [response.status_code for response in responses] == [401] * len(responses)


def test_user_can_use_current_read_routes_and_each_role_can_read_its_me(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    project = create_project(db_session, name="읽기 권한 테스트", created_by=admin.id)
    db_session.add(ProjectAccess(project_id=project.id, user_id=member.id, granted_by=admin.id))
    analysis = Analysis(project_id=project.id, executed_by=admin.id, status="COMPLETED")
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    db_session.add(Finding(analysis_id=analysis.id, file_path="src/App.java", message="결과"))
    db_session.add(
        KisaCatalog(
            kisa_code="ROLE-006",
            category="보안기능",
            name="조회 항목",
            default_severity="LOW",
        )
    )
    db_session.commit()

    login(client, member.email)
    assert client.get("/auth/me").json() == {"email": member.email, "role": "USER"}
    assert client.get("/projects/").status_code == 200
    assert client.get("/catalog/").status_code == 200
    assert client.get("/analyses/", params={"project_id": project.id}).status_code == 200
    assert client.get("/findings/", params={"analysis_id": analysis.id}).status_code == 200

    login(client, admin.email)
    assert client.get("/auth/me").json() == {"email": admin.email, "role": "ADMIN"}


def test_database_role_not_a_jwt_role_claim_controls_admin_access(client, db_session):
    admin = create_user(db_session, email="admin@secscan.io", role="ADMIN")
    member = create_user(db_session, email="member@secscan.io", role="USER")
    csrf_token = "csrf-role-claim-test"

    member_token_with_admin_claim = create_access_token(
        {"sub": str(member.id), "role": "ADMIN", "csrf": csrf_token}
    )
    client.cookies.set(settings.SESSION_COOKIE_NAME, member_token_with_admin_claim)
    client.cookies.set(settings.CSRF_COOKIE_NAME, csrf_token)
    assert client.post(
        "/projects/", json={"name": "위조 관리자 claim"}, headers=csrf_headers(csrf_token)
    ).status_code == 403

    admin_token_with_user_claim = create_access_token(
        {"sub": str(admin.id), "role": "USER", "csrf": csrf_token}
    )
    client.cookies.set(settings.SESSION_COOKIE_NAME, admin_token_with_user_claim)
    assert client.post(
        "/projects/", json={"name": "위조 사용자 claim"}, headers=csrf_headers(csrf_token)
    ).status_code == 200
