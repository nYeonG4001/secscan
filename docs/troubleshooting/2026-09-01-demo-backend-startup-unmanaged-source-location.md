# Troubleshooting: 이전 소스 위치로 인한 백엔드 시작 실패

## 기본 정보

- 작성일: 2026-09-01
- 작성자: Codex
- 관련 에픽: E3, E7
- 관련 요구사항: SFR-007, SEC-008, TST-004
- 관련 PR 또는 커밋: `fix/demo-startup-source-location` 브랜치
- 환경: 로컬 Docker 데모 환경, Python 3.12 로컬 테스트 환경

## 문제 요약

이전 형식의 `Project.source_location` 값 하나가 있으면, 시작 시 오래된 소스 작업공간을 정리하는 과정에서 `ValueError`가 발생해 백엔드가 시작하지 못했다.

## 증상

데모 백엔드 컨테이너의 FastAPI 시작 이벤트가 다음 오류로 종료됐다.

```text
ValueError: The source location is not a managed opaque location.
```

## 재현 방법

1. `Project.source_location`에 `projects/{id}/sources/{32자리-hex}` 형식이 아닌 이전 경로를 저장한다.
2. 백엔드를 시작한다.
3. 시작 이벤트가 모든 현재 소스 위치를 `cleanup_stale_unreferenced_source_directories()`에 전달한다.

## 기대 결과

관리되지 않은 이전 경로가 남아 있어도 백엔드는 시작하고, 현재 작업공간이 관리하는 오래된 소스 디렉터리만 안전하게 정리한다.

## 실제 결과

정리 로직이 모든 `source_location`을 엄격한 불투명 경로 형식으로 해석하면서 예외가 전파돼 백엔드 시작이 중단됐다.

## 원인 분석

- 확인한 증거:
  - `backend/app/main.py`의 시작 이벤트는 NULL이 아닌 모든 `Project.source_location`을 정리 서비스에 전달한다.
  - `backend/app/services/source_workspace.py`는 관리 경로 형식이 아니면 `ValueError`를 발생시킨다.
  - 데모 데이터에 현재 형식으로 관리되지 않는 소스 위치가 존재했다.
- 원인: 이전 데이터와 엄격한 작업공간 경로 검증의 호환성 처리 부재다.
- 원인이 아니었던 가설: 작업공간 밖 경로 삭제나 경로 조작이 원인이 아니다. 정리 대상 순회는 `projects/{id}/sources/{opaque-id}` 아래의 실제 관리 디렉터리에만 한정된다.

## 해결 방법

- 변경 파일:
  - `backend/app/services/source_workspace.py`
  - `backend/app/main.py`
  - `backend/tests/test_source_workspace.py`
  - `backend/tests/test_source_upload_api.py`
- 변경 내용:
  - 관리 형식이 아닌 소스 위치는 참조 목록 구성에서 제외한다.
  - 시작 이벤트는 제외된 이전 경로의 개수를 경고 로그로 남긴다.
  - 정상 관리 경로는 계속 참조 목록에 남아 삭제 대상에서 보호한다.
  - 이전 경로와 정상 참조·오래된 미참조 경로가 섞인 회귀 테스트를 추가한다.

## 검증

- [x] 같은 입력 형식에서 시작 정리가 예외 없이 완료됨
- [x] 관련 단위 테스트 통과
- [x] 기존 기능 회귀 확인
- [x] 보안 영향 확인
- [ ] 실제 데모 컨테이너 재시작 후 화면 확인

```text
TEST_DATABASE_URL=<전용_테스트_DB_URL> \
STORAGE_ROOT=/tmp/secscan-backend-startup-fix-storage \
python -m pytest -q backend/tests/test_source_workspace.py \
  backend/tests/test_source_upload_api.py -k 'cleanup_ignores_unmanaged or startup_sweep'

2 passed, 26 deselected

python -m pytest -q -k 'not real_semgrep'

209 passed, 6 deselected

ruff check backend/app/main.py backend/app/services/source_workspace.py \
  backend/tests/test_source_workspace.py backend/tests/test_source_upload_api.py

All checks passed
```

로컬 macOS 환경에서 실제 Semgrep fixture 6건은 자원 제한 종료로 별도 실패했다. 이번 시작 정리 변경과는 무관하며, CI 또는 Linux Docker 환경에서 실규칙 검증을 다시 확인한다.

## 남은 위험과 후속 작업

- 남은 문제: 이전 소스 위치는 시작 시 경고만 남기며, 자동 마이그레이션하거나 삭제하지 않는다.
- 후속 작업: 실제 데모 컨테이너 재시작 뒤 `/health`, 프로젝트 목록, 완료된 분석 결과, 카탈로그 조회를 확인한다. 이전 경로의 장기 처리 정책은 데이터 보존 요구를 검토한 뒤 별도 결정한다.
- 관련 문서 업데이트: E7 검증 증거에 실제 데모 재시작 결과를 추가한다.

## 참고 자료

- 로그 경로: Docker 컨테이너 `secscan-demo-fresh-backend-1` 시작 로그
- 관련 코드: `backend/app/main.py`, `backend/app/services/source_workspace.py`
- 리뷰: `.omx/artifacts/claude-review-the-current-git-diff-for-a-small-fastapi-startup-swee-2026-08-31T16-05-50-137Z.md`
