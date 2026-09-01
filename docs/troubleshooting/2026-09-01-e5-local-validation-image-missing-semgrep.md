# Troubleshooting: E5 로컬 검증 이미지의 Semgrep CLI 누락

## 기본 정보

- 작성일: 2026-09-01
- 작성자: Codex
- 관련 에픽: E5, E7
- 관련 요구사항: SFR-010, SFR-011, TST-004, TST-005
- 관련 PR 또는 커밋: 없음
- 환경: 로컬 Docker

## 문제 요약

기존 로컬 `secscan-backend:latest` 이미지에 `semgrep` 실행 파일이 없어 실제 fixture 정규화 테스트가 실행 엔진 오류로 실패했다.

## 증상

`test_e5_result_normalization.py`의 실제 Semgrep fixture 12개가 같은 이유로 실패했다.

```text
FileNotFoundError: [Errno 2] No such file or directory
... semgrep_wrapper.py ... os.execvp(..., "semgrep", ...)
```

## 재현 방법

1. 기존 `secscan-backend:latest` 이미지를 사용해 `SemgrepRunner.run()`을 실행한다.
2. 실행기가 구성한 `semgrep` 명령을 기존 리소스 래퍼로 시작한다.
3. 이미지에 CLI가 없어 `os.execvp`가 실패한다.

## 기대 결과

현재 `backend/Dockerfile`이 고정한 Semgrep OSS 1.95.0이 이미지에 있어 fixture 분석이 실행돼야 한다.

## 실제 결과

기존 태그 이미지는 현재 Dockerfile 기준으로 빌드된 이미지가 아니어서 모든 실제 fixture가 `ENGINE_EXECUTION_FAILED`로 종료됐다.

## 원인 분석

- 확인한 증거: 동일한 fixture를 Semgrep OSS 1.95.0 컨테이너에서 직접 실행하면 규칙 결과가 나왔고, 기존 백엔드 이미지의 래퍼 실행은 `FileNotFoundError`로 종료됐다.
- 원인: 로컬 `secscan-backend:latest` 이미지가 현재 `backend/requirements.txt`의 Semgrep 의존성을 포함하지 않는 오래된 이미지였다.
- 원인이 아니었던 가설: 신규 규칙 YAML 문법 또는 `ANALYSIS_RESOURCE_LIMIT`.

## 해결 방법

- 변경 파일: 없음
- 변경 내용: 현재 `backend/Dockerfile`로 일회성 `secscan-e5-validation-backend:local` 검증 이미지를 다시 빌드했다. Semgrep 실행 래퍼와 리소스 제한 코드는 바꾸지 않았다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 테스트 통과
- [ ] 전체 회귀 없음
- [x] 보안 영향 확인

```text
docker build --tag secscan-e5-validation-backend:local backend
pytest -q tests/test_e5_result_normalization.py
32 passed

ruff check app tests
All checks passed

# 아래 직접 실행은 신규 source 형태의 대표 fixture를 확인한 명령이다.
# 전체 fixture 검증은 위 pytest가 변경하지 않은 SemgrepRunner를 통해 수행한다.
docker run --rm \
  -v backend/semgrep-rules:/rules:ro \
  -v backend/tests/fixtures/vulnerable:/vulnerable:ro \
  semgrep/semgrep:1.95.0 semgrep \
  --config /rules/secscan-security.yml --no-rewrite-rule-ids \
  --json --quiet --oss-only --metrics=off \
  /vulnerable/JdbcStatementSql.java \
  /vulnerable/JdbcStatementUpdateSql.java \
  /vulnerable/dom_innerhtml.js \
  /vulnerable/dom_innerhtml_arrow.js \
  /vulnerable/open_user_path.py
```

## 남은 위험과 후속 작업

- 남은 문제: GitHub Actions Ubuntu의 필터 없는 `pytest -q`는 push/PR 금지 범위 밖이다.
- 후속 작업: 사람 검토와 병합 전 CI에서 전체 fixture를 확인한다.
- 관련 문서 업데이트: `docs/epic/e5-result-normalization.md`, `docs/requirements-matrix.md`

## 참고 자료

- 로그 경로: 현재 E5 구현 작업 세션의 Docker 테스트 출력
- 화면 캡처: 없음
- 관련 커밋: 없음
