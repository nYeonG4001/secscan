# ADR-002: 기술 스택

**Context**: Semgrep을 서브프로세스로 호출하므로, 같은 환경에 pip으로 함께 설치되는 Python 백엔드가 툴체인을 단순하게 유지시켜줌.

**Decision**: Python + FastAPI + SQLAlchemy/Alembic + PostgreSQL(JSONB) + React(Vite, TS) + Tailwind/shadcn + Docker Compose

**Alternatives**: Java/Spring(기각: Semgrep용 Python 런타임을 이미지에 별도로 넣어야 함), Node/Express(기각: 타입검증·문서화 생태계가 FastAPI+Pydantic 대비 약함)

**Consequences**: Swagger 자동생성으로 검수 편의 ↑, Pydantic으로 결과 스키마 강제 / FastAPI는 Spring만큼 구조를 강제하지 않아 직접 설계 필요
