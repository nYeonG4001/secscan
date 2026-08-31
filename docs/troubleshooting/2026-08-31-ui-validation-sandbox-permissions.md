# Troubleshooting: 제한된 실행 환경의 프론트엔드·Docker 검증 권한

## 기본 정보

- 작성일: 2026-08-31
- 작성자: Codex
- 관련 에픽: E6
- 관련 요구사항: QLT-004, QLT-005
- 관련 PR 또는 커밋: `feat/ui-pen-alignment` 후속 변경
- 환경: 로컬 제한 실행 환경 / Docker

## 문제 요약

제한된 실행 환경에서 Vite가 생성하는 임시 설정 파일과 Docker 소켓에 접근하지 못해 검증 명령이 시작되지 않았다.

## 증상

```text
Error: EPERM: operation not permitted, open
'.../frontend/vite.config.ts.timestamp-....mjs'

permission denied while trying to connect to the docker API
at unix:///Users/erwne/.docker/run/docker.sock
```

## 재현 방법

1. 제한된 파일시스템 권한으로 `frontend/`에서 `npm test`를 실행한다.
2. 같은 환경에서 `docker ps`를 실행한다.

## 기대 결과

Vite/Vitest가 임시 설정 파일을 만들고, Docker 기반의 별도 PostgreSQL 검증 환경을 사용할 수 있어야 한다.

## 실제 결과

첫 번째 명령은 Vite 설정 임시 파일 생성에서, 두 번째 명령은 Docker 소켓 연결에서 권한 오류가 발생했다.

## 원인 분석

- 확인한 증거: 동일 작업트리에서 필요한 권한으로 재실행한 뒤 Vitest와 Docker 기반 검증이 진행됐다.
- 원인: 저장소 코드나 의존성 문제가 아니라 제한된 실행 환경의 파일시스템·Docker 소켓 접근 정책이다.
- 원인이 아니었던 가설: Vite 설정 문법 오류, 프론트엔드 테스트 실패, PostgreSQL 스키마 오류.

## 해결 방법

- 변경 파일: 없음
- 변경 내용: 임시 파일과 Docker 소켓 접근이 가능한 검증 환경에서만 해당 명령을 실행한다. 데모 DB는 사용하지 않고 이름이 `_test`로 끝나는 별도 PostgreSQL 컨테이너를 사용한다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
cd frontend && npm run lint && npm test && npm run typecheck && npm run build
→ lint 통과, 4 files / 44 tests 통과, typecheck·build 통과

Python 3.12 Docker + 별도 PostgreSQL _test DB
→ ruff check app tests: All checks passed
→ pytest -q: 실행 완료
```

## 남은 위험과 후속 작업

- 남은 문제: 제한된 실행 환경에서는 같은 권한 오류가 다시 발생할 수 있다.
- 후속 작업: CI에서는 일반 Linux runner 권한으로 검증한다.
- 관련 문서 업데이트: 없음

## 참고 자료

- 로그 경로: 로컬 에이전트 실행 로그
- 화면 캡처: 없음
- 관련 커밋: 커밋 예정
