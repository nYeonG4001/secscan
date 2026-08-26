# SecScan

KISA 개발보안가이드 기반 SAST 웹앱

교육 기간: 2026-08-25부터 2026-09-03까지
MVP는 이번 프로젝트에서 구현할 최소 기능 범위를 의미하며, 교육 기간 자체와 같은 개념으로 사용하지 않는다.

## 로컬 실행

### 사전 요구 사항
- Docker Desktop (또는 Docker + Docker Compose v2)

### 1. 환경 변수 준비

`.env.example`을 복사해 `.env`를 만들고, 시드 계정 비밀번호와 `SECRET_KEY`를 직접 입력합니다.

```bash
cp .env.example .env

set -a
source .env
set +a
```

`.env`는 Git에 커밋하지 않습니다.

### 2. 전체 실행

```bash
cd /Users/erwne/white/SecScan
docker compose up --build
```

- PostgreSQL: `localhost:5432`
- Backend API: `http://localhost:8000` (Swagger: `http://localhost:8000/docs`)
- Frontend: `http://localhost:5173`

### 3. 시드 계정

시드 계정 이메일과 비밀번호는 `.env`의 다음 변수로 설정합니다.

```text
ADMIN_SEED_EMAIL
ADMIN_SEED_PASSWORD
USER_SEED_EMAIL
USER_SEED_PASSWORD
```

### 4. 로그인 API 직접 테스트

```bash
curl -X POST http://localhost:8000/auth/login \
  -H "Content-Type: application/json" \
  -d "{\"email\":\"$ADMIN_SEED_EMAIL\",\"password\":\"$ADMIN_SEED_PASSWORD\"}"
```

### 5. 마이그레이션 단독 실행 (컨테이너 내부)

```bash
docker compose exec backend alembic upgrade head
```

### 6. 서비스 재시작 없이 코드 반영

백엔드는 `--reload` 옵션으로 실행되므로, `./backend` 내 파일 수정 시 자동 반영됩니다.
프론트엔드는 Vite HMR로 `./frontend/src` 수정 시 자동 반영됩니다.

## 프로젝트 구조

```
SecScan/
├── backend/
│   ├── app/
│   │   ├── core/        # config, database, security, deps
│   │   ├── models/      # SQLAlchemy ORM (ERD 그대로)
│   │   ├── schemas/     # Pydantic 스키마
│   │   ├── routers/     # auth, projects, analyses, findings, catalog
│   │   └── services/    # 비즈니스 로직 (향후 확장)
│   ├── alembic/         # DB 마이그레이션
│   ├── seed.py          # 시드 계정 생성
│   └── requirements.txt
├── frontend/
│   └── src/
│       ├── pages/       # 6개 화면 (LoginPage 백엔드 연동)
│       └── api/         # axios 래퍼
├── docker-compose.yml
└── docs/                # 설계 문서 (ADR, ERD, MVP)
```

## 기술 스택

- **백엔드**: Python 3.12 + FastAPI + SQLAlchemy 2.0 + Alembic + PostgreSQL
- **프론트**: React 18 + Vite + TypeScript + Tailwind CSS
- **배포**: Docker Compose
