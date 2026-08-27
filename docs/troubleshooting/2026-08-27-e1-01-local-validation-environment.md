# Troubleshooting: E1-01 로컬 검증 도구와 Docker 데몬 미가동

## 기본 정보

- 작성일: 2026-08-27
- 작성자: Codex
- 관련 에픽: E1-01
- 관련 요구사항: SFR-001, SFR-002, SFR-003, DAR-002, SEC-001, SEC-002
- 관련 PR 또는 커밋: 없음
- 환경: 로컬 / Docker

## 문제 요약

로컬 환경에서 E1-01의 pytest, ruff, Alembic 마이그레이션 검증을 실행할 수 없다.

## 증상

```text
python3 -m ruff check app tests
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: No module named ruff

python3 -m pytest -q tests/test_user_model.py tests/test_auth_api.py
/Applications/Xcode.app/Contents/Developer/usr/bin/python3: No module named pytest

docker version --format '{{.Server.Version}}'
failed to connect to the docker API at unix:///Users/erwne/.docker/run/docker.sock
```

## 재현 방법

1. 저장소 루트에서 `cd backend`를 실행한다.
2. `python3 -m ruff check app tests` 또는 `python3 -m pytest -q`를 실행한다.
3. 저장소 루트에서 `docker version --format '{{.Server.Version}}'`를 실행한다.

## 기대 결과

Python 3.12 개발 의존성과 PostgreSQL 테스트 DB를 사용해 E1-01의 린트, 단위·인증 테스트, Alembic upgrade/downgrade 검증이 실행된다.

## 실제 결과

시스템 Python은 3.9.6이며 개발 의존성이 설치되지 않았고, Docker CLI는 있으나 Docker 데몬이 실행되지 않았다.

## 원인 분석

- 확인한 증거: `backend/requirements-dev.txt`에 pytest와 ruff가 선언돼 있지만 로컬 Python 환경에는 설치되지 않았다. `backend/Dockerfile`은 운영 의존성만 설치한다.
- 원인: Python 3.12 개발 환경과 Docker 데몬이 준비되지 않았다.
- 원인이 아니었던 가설: E1-01 소스의 문법 오류. 변경 Python 파일과 새 migration은 AST 파싱에 성공했다.

## 해결 방법

- 변경 파일: 없음 (환경 준비만 필요했다)
- 변경 내용: Docker Desktop을 실행하고, 전용 테스트 Postgres 컨테이너(`secscan_test`)를 띄우고, Python 3.12 venv에 `requirements-dev.txt`를 설치해 실제 검증을 진행했다. 검증 도중 발견된 별도의 코드 버그 2건은 `docs/troubleshooting/2026-08-27-e1-01-email-domain-and-migration-test-bugs.md`에 기록했다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
git diff --check
성공

python3 AST 파싱 및 Alembic revision graph 확인
성공: revision=0002, down_revision=0001

cd backend && export TEST_DATABASE_URL=postgresql://secscan:secscan@localhost:5433/secscan_test SECRET_KEY=test-secret-key
.venv/bin/ruff check .        → All checks passed!
.venv/bin/python -m pytest -q → 19 passed (3회 연속 재실행)
```

## 남은 위험과 후속 작업

- 남은 문제: 없음. Docker/Python 3.12 환경 준비 후 린트·단위·인증·마이그레이션 테스트가 모두 통과했다.
- 후속 작업: 없음.
- 관련 문서 업데이트: `docs/troubleshooting/2026-08-27-e1-01-email-domain-and-migration-test-bugs.md` 신규 작성

## 참고 자료

- 로그 경로: 현재 작업 세션의 명령 출력
- 화면 캡처: 없음
- 관련 커밋: 없음
