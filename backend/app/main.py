import logging
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.deps import get_analysis_executor, get_source_workspace
from app.models.analysis import Analysis
from app.models.project import Project
from app.routers import analyses, auth, catalog, findings, projects

logger = logging.getLogger(__name__)

app = FastAPI(
    title="SecScan API",
    version="0.1.0",
    description="KISA 개발보안가이드 기반 SAST 웹앱",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(projects.router)
app.include_router(analyses.router)
app.include_router(findings.router)
app.include_router(catalog.router)


@app.get("/health", tags=["health"])
def health():
    return {"status": "ok"}


@app.on_event("startup")
def recover_interrupted_analyses_and_sweep_stale_workspaces() -> None:
    retention = timedelta(hours=settings.STALE_WORKSPACE_RETENTION_HOURS)
    workspace = get_source_workspace()
    db = SessionLocal()
    try:
        interrupted = (
            db.query(Analysis)
            .filter(Analysis.status.in_(["PENDING", "RUNNING"]))
            .update(
                {
                    Analysis.status: "FAILED",
                    Analysis.error_code: "ANALYSIS_INTERRUPTED",
                    Analysis.error_message: "서버 중단으로 분석이 완료되지 않았습니다.",
                    Analysis.execution_log: "서버 중단으로 분석이 완료되지 않았습니다.",
                    Analysis.completed_at: datetime.now(timezone.utc),
                },
                synchronize_session=False,
            )
        )
        db.commit()
        current_locations = [
            loc
            for (loc,) in db.query(Project.source_location)
            .filter(Project.source_location.isnot(None))
            .all()
        ]
    finally:
        db.close()
    removed_staging = workspace.cleanup_stale_staging_directories(retention)
    removed_sources = workspace.cleanup_stale_unreferenced_source_directories(
        current_locations, retention
    )
    unmanaged_location_count = sum(
        not workspace.is_managed_source_location(location)
        for location in current_locations
    )
    if removed_staging or removed_sources:
        logger.info(
            "Startup sweep removed %d staging and %d unreferenced source directories",
            len(removed_staging),
            len(removed_sources),
        )
    if unmanaged_location_count:
        logger.warning(
            "Startup sweep ignored %d unmanaged project source location(s)",
            unmanaged_location_count,
        )
    if interrupted:
        logger.warning("Startup marked %d interrupted analyses as failed", interrupted)


@app.on_event("shutdown")
def shutdown_analysis_executor() -> None:
    get_analysis_executor().shutdown()
    get_analysis_executor.cache_clear()
