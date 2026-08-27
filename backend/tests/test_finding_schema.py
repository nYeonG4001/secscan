from app.core.security import hash_password
from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.kisa_catalog import KisaCatalog
from app.models.project import Project
from app.models.user import User
from app.schemas.finding import FindingAdminOut, FindingUserOut


def create_user(db_session, *, email: str, role: str = "ADMIN") -> User:
    user = User(email=email, password_hash=hash_password("password"), role=role)
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


def create_analysis(db_session, *, project_id: int, executed_by: int) -> Analysis:
    analysis = Analysis(project_id=project_id, executed_by=executed_by, status="COMPLETED")
    db_session.add(analysis)
    db_session.commit()
    db_session.refresh(analysis)
    return analysis


def create_catalog_item(
    db_session, *, kisa_code: str, criterion_id: str, recommendation: str
) -> KisaCatalog:
    item = KisaCatalog(
        kisa_code=kisa_code,
        criterion_id=criterion_id,
        category="입력데이터 검증 및 표현",
        name="SQL 삽입",
        default_severity="HIGH",
        recommendation=recommendation,
    )
    db_session.add(item)
    db_session.commit()
    db_session.refresh(item)
    return item


def test_finding_can_be_created_with_all_new_fields(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="진단 결과 필드 테스트", created_by=admin.id)
    analysis = create_analysis(db_session, project_id=project.id, executed_by=admin.id)
    catalog_item = create_catalog_item(
        db_session, kisa_code="SEC-001", criterion_id="3.1", recommendation="입력값을 검증하세요."
    )

    finding = Finding(
        analysis_id=analysis.id,
        kisa_code=catalog_item.kisa_code,
        criterion_id=catalog_item.criterion_id,
        rule_name="SQL 삽입",
        severity="HIGH",
        confidence="HIGH",
        language="JAVA",
        file_path="src/main/java/App.java",
        line=42,
        message="사용자 입력이 검증 없이 쿼리에 사용됩니다.",
        evidence="String query = \"SELECT * FROM users WHERE id=\" + userId;",
        recommendation=catalog_item.recommendation,
        raw_result={"tool": "semgrep", "check_id": "java.sql-injection"},
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    assert finding.criterion_id == "3.1"
    assert finding.evidence.startswith("String query")
    assert finding.recommendation == "입력값을 검증하세요."
    assert finding.raw_result == {"tool": "semgrep", "check_id": "java.sql-injection"}


def test_unmapped_finding_stores_normally_without_kisa_code(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="미매핑 결과 테스트", created_by=admin.id)
    analysis = create_analysis(db_session, project_id=project.id, executed_by=admin.id)

    finding = Finding(
        analysis_id=analysis.id,
        kisa_code=None,
        criterion_id=None,
        file_path="src/index.js",
        line=10,
        message="미매핑 규칙에서 탐지됨",
        evidence="eval(userInput);",
        raw_result={"tool": "semgrep", "check_id": "generic.eval-usage"},
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    assert finding.kisa_code is None
    assert finding.criterion_id is None
    assert finding.evidence == "eval(userInput);"
    assert finding.raw_result == {"tool": "semgrep", "check_id": "generic.eval-usage"}


def test_finding_snapshot_is_independent_of_catalog_changes(db_session):
    admin = create_user(db_session, email="admin@secscan.io")
    project = create_project(db_session, name="스냅샷 불변성 테스트", created_by=admin.id)
    analysis = create_analysis(db_session, project_id=project.id, executed_by=admin.id)
    catalog_item = create_catalog_item(
        db_session, kisa_code="SEC-002", criterion_id="3.2", recommendation="원래 권고 문구"
    )

    finding = Finding(
        analysis_id=analysis.id,
        kisa_code=catalog_item.kisa_code,
        criterion_id=catalog_item.criterion_id,
        file_path="src/main/java/App.java",
        recommendation=catalog_item.recommendation,
    )
    db_session.add(finding)
    db_session.commit()
    db_session.refresh(finding)

    catalog_item.criterion_id = "9.9"
    catalog_item.recommendation = "변경된 권고 문구"
    db_session.commit()
    db_session.refresh(finding)

    assert finding.criterion_id == "3.2"
    assert finding.recommendation == "원래 권고 문구"
    assert catalog_item.criterion_id == "9.9"
    assert catalog_item.recommendation == "변경된 권고 문구"


def test_finding_out_schemas_include_new_snapshot_fields():
    assert {"criterion_id", "evidence", "recommendation"} <= set(FindingUserOut.model_fields)
    assert "raw_result" not in FindingUserOut.model_fields
    assert "raw_result" in FindingAdminOut.model_fields
