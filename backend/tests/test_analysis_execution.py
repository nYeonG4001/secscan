from app.models.analysis import Analysis
from app.models.finding import Finding
from app.models.project import Project
from app.models.user import User
from app.services.analysis_executor import AnalysisExecutor
from app.services.semgrep_runner import SemgrepRunError, SemgrepRunResult
from app.services.source_workspace import SourceWorkspace


class SuccessfulRunner:
    def run(self, snapshot_root):
        assert (snapshot_root / "src" / "App.java").is_file()
        return SemgrepRunResult(
            result_count=2,
            results=[],
            metadata={"engine": "semgrep", "result_count": 2},
            execution_log=None,
        )


class FailingRunner:
    def run(self, snapshot_root):
        raise SemgrepRunError(
            "ENGINE_OUTPUT_INVALID",
            "분석 엔진 출력 형식이 올바르지 않습니다.",
            "안전한 진단 로그",
        )


class MalformedResultsRunner:
    def run(self, snapshot_root):
        return SemgrepRunResult(
            result_count=2,
            results=[
                {
                    "check_id": "unmapped.rule",
                    "path": "src/App.java",
                    "start": {"line": 1},
                    "end": {"line": 1},
                    "extra": {
                        "message": "정상 결과",
                        "severity": "WARNING",
                        "metadata": {},
                    },
                },
                {"check_id": "malformed"},
            ],
            metadata={"engine": "semgrep", "result_count": 2},
            execution_log=None,
        )


def _create_analysis(db_session, workspace):
    admin = User(email="executor@secscan.io", password_hash="hash", role="ADMIN")
    db_session.add(admin)
    db_session.commit()
    project = Project(name="실행기 프로젝트", created_by=admin.id, target_languages=["JAVA"])
    db_session.add(project)
    db_session.commit()
    staging = workspace.create_staging_directory()
    (staging / "src").mkdir()
    (staging / "src" / "App.java").write_text("class App {}")
    project.source_location = workspace.promote_staging_directory(project.id, staging)
    db_session.commit()
    analysis = Analysis(
        project_id=project.id,
        executed_by=admin.id,
        status="PENDING",
        source_location=project.source_location,
    )
    db_session.add(analysis)
    db_session.commit()
    analysis.source_snapshot_location = workspace.reserve_analysis_snapshot(analysis.id)
    db_session.commit()
    return analysis


def test_executor_copies_captured_source_and_completes(db_session, tmp_path, monkeypatch):
    workspace = SourceWorkspace(tmp_path / "storage")
    analysis = _create_analysis(db_session, workspace)
    monkeypatch.setattr("app.services.analysis_executor.get_source_workspace", lambda: workspace)

    AnalysisExecutor(runner=SuccessfulRunner())._execute(analysis.id)

    db_session.refresh(analysis)
    assert analysis.status == "COMPLETED"
    assert analysis.started_at is not None
    assert analysis.completed_at is not None
    assert analysis.summary == {"total_findings": 0}
    assert analysis.raw_result == {"engine": "semgrep", "result_count": 2}
    snapshot = workspace.resolve_analysis_snapshot_location(analysis.source_snapshot_location)
    assert (snapshot / "src/App.java").is_file()


def test_executor_records_safe_engine_failure(db_session, tmp_path, monkeypatch):
    workspace = SourceWorkspace(tmp_path / "storage")
    analysis = _create_analysis(db_session, workspace)
    monkeypatch.setattr("app.services.analysis_executor.get_source_workspace", lambda: workspace)

    AnalysisExecutor(runner=FailingRunner())._execute(analysis.id)

    db_session.refresh(analysis)
    assert analysis.status == "FAILED"
    assert analysis.error_code == "ENGINE_OUTPUT_INVALID"
    assert analysis.execution_log == "안전한 진단 로그"


def test_executor_rolls_back_all_findings_when_one_result_is_invalid(
    db_session, tmp_path, monkeypatch
):
    workspace = SourceWorkspace(tmp_path / "storage")
    analysis = _create_analysis(db_session, workspace)
    monkeypatch.setattr("app.services.analysis_executor.get_source_workspace", lambda: workspace)

    AnalysisExecutor(runner=MalformedResultsRunner())._execute(analysis.id)

    db_session.refresh(analysis)
    assert analysis.status == "FAILED"
    assert analysis.error_code == "ENGINE_OUTPUT_INVALID"
    assert db_session.query(Finding).filter_by(analysis_id=analysis.id).count() == 0
