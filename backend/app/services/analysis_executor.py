"""In-process, single-worker analysis execution (ADR-022)."""

from __future__ import annotations

import logging
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone

from app.core.database import SessionLocal
from app.core.deps import get_source_workspace
from app.models.analysis import Analysis
from app.services.semgrep_runner import SemgrepRunError, SemgrepRunner

logger = logging.getLogger(__name__)


class AnalysisExecutor:
    def __init__(self, runner: SemgrepRunner | None = None) -> None:
        self.runner = runner or SemgrepRunner()
        self._pool = ThreadPoolExecutor(max_workers=1, thread_name_prefix="secscan-analysis")

    def submit(self, analysis_id: int) -> None:
        self._pool.submit(self._execute, analysis_id)

    def shutdown(self) -> None:
        self._pool.shutdown(wait=False, cancel_futures=True)

    def _execute(self, analysis_id: int) -> None:
        db = SessionLocal()
        try:
            analysis = db.get(Analysis, analysis_id)
            if not analysis or analysis.status != "PENDING":
                return
            analysis.status = "RUNNING"
            analysis.started_at = datetime.now(timezone.utc)
            db.commit()

            try:
                if not analysis.source_location or not analysis.source_snapshot_location:
                    raise ValueError("Captured source is missing.")
                snapshot_root = get_source_workspace().copy_source_to_snapshot(
                    analysis.source_location, analysis.source_snapshot_location
                )
            except Exception:
                logger.exception("Analysis snapshot creation failed for analysis %d", analysis_id)
                self._fail(
                    db,
                    analysis,
                    "SOURCE_SNAPSHOT_FAILED",
                    "소스 스냅샷을 만들지 못했습니다.",
                )
                return

            try:
                result = self.runner.run(snapshot_root)
            except SemgrepRunError as exc:
                self._fail(db, analysis, exc.error_code, exc.message, exc.execution_log)
                return
            except Exception:
                logger.exception("Unexpected analysis engine failure for analysis %d", analysis_id)
                self._fail(
                    db,
                    analysis,
                    "ENGINE_EXECUTION_FAILED",
                    "분석 엔진 실행에 실패했습니다.",
                )
                return

            analysis.status = "COMPLETED"
            analysis.completed_at = datetime.now(timezone.utc)
            analysis.summary = {"total_findings": result.result_count}
            analysis.raw_result = result.metadata
            analysis.execution_log = result.execution_log
            db.commit()
        finally:
            db.close()

    @staticmethod
    def _fail(
        db, analysis: Analysis, error_code: str, message: str, execution_log: str | None = None
    ) -> None:
        analysis.status = "FAILED"
        analysis.completed_at = datetime.now(timezone.utc)
        analysis.error_code = error_code
        analysis.error_message = message
        analysis.execution_log = execution_log
        db.commit()
