import pytest
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.core.database import SessionLocal, get_db
from app.core.security import hash_password
from app.main import app
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
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


@pytest.fixture
def analysis(db_session: Session):
    user = User(email="e6-admin@example.com", password_hash=hash_password("password"), role="ADMIN")
    db_session.add(user)
    db_session.commit()
    project = Project(name="E6 결과", created_by=user.id)
    db_session.add(project)
    db_session.commit()
    analysis = Analysis(project_id=project.id, executed_by=user.id, status="COMPLETED")
    db_session.add(analysis)
    db_session.add_all(
        [
            KisaCatalog(kisa_code="KISA-001", category="테스트", name="테스트 1", default_severity="HIGH", implementation_status="지원"),
            KisaCatalog(kisa_code="KISA-002", category="테스트", name="테스트 2", default_severity="HIGH", implementation_status="지원"),
        ]
    )
    db_session.commit()
    for values in [
        {"severity": "LOW", "file_path": "b.py", "line": None, "language": "PYTHON"},
        {"severity": "HIGH", "file_path": "b.py", "line": 5, "language": "PYTHON", "kisa_code": "KISA-001"},
        {"severity": "HIGH", "file_path": "a.py", "line": 2, "language": "JAVA"},
        {"severity": "CRITICAL", "file_path": "z.py", "line": 1, "language": "JAVASCRIPT", "kisa_code": "KISA-002"},
    ]:
        db_session.add(Finding(analysis_id=analysis.id, engine_rule_id="e6.rule", **values))
    db_session.commit()
    return analysis


def auth_headers(client: TestClient) -> dict[str, str]:
    response = client.post("/auth/login", json={"email": "e6-admin@example.com", "password": "password"})
    assert response.status_code == 200
    return {"X-CSRF-Token": client.cookies.get("secscan_csrf")}


def test_list_filters_orders_and_omits_detail_fields(client: TestClient, analysis: Analysis):
    response = client.get(
        "/findings/",
        params={"analysis_id": analysis.id, "mapping_status": "KISA_MAPPED", "language": "JAVASCRIPT", "limit": 1},
        headers=auth_headers(client),
    )
    assert response.status_code == 200
    body = response.json()
    assert body["total"] == 1
    assert body["limit"] == 1
    assert body["items"][0]["mapping_status"] == "KISA_MAPPED"
    assert {"message", "evidence", "code_snippet", "recommendation", "raw_result", "engine_rule_id", "criterion_id"}.isdisjoint(body["items"][0])

    ordered = client.get("/findings/", params={"analysis_id": analysis.id}, headers=auth_headers(client)).json()
    assert [item["severity"] for item in ordered["items"]] == ["CRITICAL", "HIGH", "HIGH", "LOW"]
    assert [item["file_path"] for item in ordered["items"]][1:3] == ["a.py", "b.py"]


@pytest.mark.parametrize("params", [{"limit": 0}, {"limit": 101}, {"offset": -1}, {"language": "GO"}])
def test_list_rejects_invalid_pagination_and_language(client: TestClient, analysis: Analysis, params):
    response = client.get("/findings/", params={"analysis_id": analysis.id, **params}, headers=auth_headers(client))
    assert response.status_code == 422
