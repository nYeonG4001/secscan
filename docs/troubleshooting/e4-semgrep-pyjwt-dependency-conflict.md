# Troubleshooting: E4 Semgrep과 PyJWT 의존성 충돌

## 기본 정보

- 작성일: 2026-08-28
- 작성자: Codex
- 관련 에픽: E4
- 관련 요구사항: SEC-010, TST-004
- 관련 PR 또는 커밋: E4 구현 PR #30
- 환경: Docker

## 문제 요약

최신 Semgrep OSS CLI 1.164.0 추가 뒤 기존 backend 고정 의존성과의 전이 의존성 충돌로 이미지가 빌드되지 않았다.

Semgrep 1.95.0으로 호환 범위를 조정한 뒤에는 Python base image의 setuptools 84가 제공하지 않는 `pkg_resources`를 Semgrep이 가져와 CLI 시작이 실패했다.

## 증상

```text
semgrep 1.164.0 depends on pyjwt~=2.12.0
The user requested PyJWT==2.9.0
ERROR: ResolutionImpossible

ModuleNotFoundError: No module named 'pkg_resources'

mcp 1.23.3 depends on uvicorn>=0.31.1
The user requested uvicorn==0.30.6
ERROR: ResolutionImpossible
```

## 재현 방법

1. `backend/requirements.txt`에 `semgrep==1.164.0`과 기존 backend 고정 의존성을 둔다.
2. `docker build -t secscan-e4-test ./backend`를 실행한다.
3. Semgrep CLI를 실행한다.

## 기대 결과

고정 Semgrep CLI와 기존 인증 의존성을 함께 설치한 backend 이미지가 빌드되어야 한다.

## 실제 결과

초기에는 pip 의존성 해석이 실패했고, 호환 Semgrep 버전으로 조정한 뒤에는 CLI가 `pkg_resources` 누락으로 시작하지 못했다.

## 원인 분석

- 확인한 증거: Docker 빌드의 pip 해석 오류가 Semgrep 1.164.0의 `pyjwt~=2.12.0` 요구를 명시했다.
- 원인: Semgrep 1.164.0이 요구하는 PyJWT, Pydantic, Uvicorn 전이 의존성 범위가 기존 backend의 고정 버전과 호환되지 않았다. Semgrep 1.95.0은 `pkg_resources`를 사용하지만 base image의 setuptools 84는 이를 제공하지 않았다.
- 원인이 아니었던 가설: Docker 캐시 또는 네트워크 오류가 아니었다.

## 해결 방법

- 변경 파일: `backend/requirements.txt`
- 변경 내용: Semgrep OSS CLI를 프로젝트의 고정 backend 의존성과 호환되는 1.95.0으로 고정하고, `pkg_resources`를 제공하는 `setuptools==80.9.0`을 명시했다. Semgrep 엔진과 자체 규칙 정책은 유지한다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
2026-08-28 검증 결과:

- Alembic `upgrade head → downgrade base → upgrade head`가 0007에서 성공
- backend 전체 pytest 195개와 `ruff check app tests` 통과
- frontend lint, 30개 Vitest, typecheck, production build 통과
- Docker에서 Semgrep OSS 1.95.0, non-root UID 999, named volume 쓰기, Compose 1.5 GiB 제한 확인
```

## 남은 위험과 후속 작업

- 남은 문제: 없음.
- 후속 작업: Semgrep 및 PyJWT 업데이트 때 두 패키지의 호환성을 함께 확인한다.
- 관련 문서 업데이트: `backend/THIRD_PARTY_NOTICES.md`

## 참고 자료

- 로그 경로: Docker build 출력
- 화면 캡처: 해당 없음
- 관련 커밋: E4 구현 PR #30
