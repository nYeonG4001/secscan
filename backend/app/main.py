from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import analyses, auth, catalog, findings, projects

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
