# Troubleshooting: E5 Docker 집중 검증 환경 분리

## 기본 정보

- 작성일: 2026-09-01
- 작성자: Codex
- 관련 에픽: E5, E7
- 관련 요구사항: SFR-010, SFR-011, TST-004, TST-005, SEC-010
- 관련 PR 또는 커밋: 없음
- 환경: 로컬 Docker

## 문제 요약

로컬 Docker Compose의 PostgreSQL 호스트 포트 충돌과 backend 운영 이미지의 개발 의존성 부재로, Compose 서비스 안에서 E5 집중 pytest를 바로 실행할 수 없었다.

## 증상

`docker compose up --build --detach`는 DB의 `5432` 바인딩에서 실패했고, 새 backend 운영 이미지에서 `pytest`를 실행하면 명령을 찾지 못했다. 읽기 전용 소스 마운트에서 Ruff 기본 캐시를 쓰려 하면 캐시 생성도 실패했다.

```text
Bind for 0.0.0.0:5432 failed: port is already allocated
sh: 1: pytest: not found
ruff failed: Read-only file system at path "/app/.ruff_cache/..."
```

## 재현 방법

1. `.env.example`을 `.env`로 복사하고 문서화된 방식으로 환경 변수를 로드한다.
2. `docker compose up --build --detach`를 실행한다.
3. Compose backend 이미지에서 `pytest -q tests/test_e5_result_normalization.py` 또는 읽기 전용 마운트에서 `ruff check .`를 실행한다.

## 기대 결과

고정 Semgrep OSS가 포함된 Linux Docker 환경에서 전용 PostgreSQL 테스트 DB를 사용해 E5 fixture 테스트와 Ruff 검증을 실행해야 한다.

## 실제 결과

기존 `secscan-test-db`가 호스트 `5432`를 사용 중이어서 Compose DB가 시작되지 않았고, 운영 backend Dockerfile은 `requirements.txt`만 설치하므로 pytest·Ruff가 없다.

## 원인 분석

- 확인한 증거: Docker 컨테이너 목록에서 `secscan-test-db`의 `0.0.0.0:5432->5432/tcp` 바인딩을 확인했고, `backend/Dockerfile`은 `requirements-dev.txt`를 설치하지 않는다.
- 원인: 로컬 공유 Docker 환경의 포트 충돌과 운영 이미지·검증 도구의 의도된 의존성 분리다.
- 원인이 아니었던 가설: ADR-040 Semgrep YAML 문법, fixture의 기대 `check_id`, KISA 매핑, Ruff 규칙 위반.

## 해결 방법

- 변경 파일: 제품 코드 없음
- 변경 내용: 포트를 공개하지 않는 임시 bridge 네트워크와 전용 PostgreSQL `_test` 컨테이너를 만들고, 현재 backend를 읽기 전용 마운트한 일회성 test-runner에 `pytest`·`httpx`·`ruff`를 설치했다. Ruff 캐시는 `RUFF_CACHE_DIR=/tmp/ruff-cache`로 컨테이너 임시 경로에만 저장했다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
Docker test-runner: pytest -q tests/test_e5_result_normalization.py
41 passed

Docker test-runner: ruff check .
All checks passed!
```

## 남은 위험과 후속 작업

- 남은 문제: GitHub Actions Ubuntu의 필터 없는 `pytest -q`는 PR CI에서 확인해야 한다.
- 후속 작업: 임시 Docker 컨테이너·네트워크를 삭제하고 PR CI 결과를 병합 전에 확인한다.
- 관련 문서 업데이트: `docs/epic/e5-result-normalization.md`, `docs/requirements-matrix.md`

## 참고 자료

- 로그 경로: Codex 작업 세션 Docker 출력
- 화면 캡처: 없음
- 관련 커밋: 없음
