import logging
from datetime import timedelta

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.database import SessionLocal
from app.core.deps import get_source_workspace
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
def sweep_stale_workspaces() -> None:
    retention = timedelta(hours=settings.STALE_WORKSPACE_RETENTION_HOURS)
    workspace = get_source_workspace()
    db = SessionLocal()
    try:
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
    if removed_staging or removed_sources:
        logger.info(
            "Startup sweep removed %d staging and %d unreferenced source directories",
            len(removed_staging),
            len(removed_sources),
        )
