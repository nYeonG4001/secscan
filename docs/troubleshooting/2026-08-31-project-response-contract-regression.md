# Troubleshooting: 프로젝트 응답 계산 필드 계약 회귀

## 기본 정보

- 작성일: 2026-08-31
- 작성자: 박하영
- 관련 에픽: E6 결과와 카탈로그 UI
- 관련 요구사항: SFR-003, SFR-015, TST-007
- 관련 PR 또는 커밋: PR #38
- 환경: GitHub Actions CI

## 문제 요약

프로젝트 목록 화면을 위해 추가한 계산 필드가 E1 종단 간 API 계약 테스트의 기대 필드 목록에 반영되지 않아 Backend test가 실패했다.

## 증상

PR #38의 Backend test에서 `test_end_to_end_flow_matches_documented_api_contract`가 실패했다.

```text
Extra items in the left set:
'source_status'
'latest_analysis_status'
```

## 재현 방법

1. 프로젝트 생성 API를 호출한다.
2. 응답 JSON의 키 집합을 `tests/test_e1_contract.py`의 `PROJECT_FIELDS`와 비교한다.
3. 계산 필드 두 개가 기대 목록에 없으면 테스트가 실패한다.

## 기대 결과

`GET /api/projects`와 프로젝트 생성·상세 응답의 필드가 API 계약과 E1 계약 테스트에서 동일하게 관리된다.

## 실제 결과

실제 응답에는 `source_status`, `latest_analysis_status`가 포함됐지만, `PROJECT_FIELDS`는 두 필드를 제외한 이전 계약을 기대했다.

## 원인 분석

- 확인한 증거: `backend/app/schemas/project.py`와 `backend/app/routers/projects.py`가 두 계산 필드를 반환하고, `docs/api-contract.md`도 두 필드를 명시한다.
- 원인: UI를 위한 프로젝트 응답 확장 시 E1 종단 간 계약 테스트의 허용 필드 목록을 함께 갱신하지 않았다.
- 원인이 아니었던 가설: 프로젝트 응답 직렬화나 계산 상태 로직의 오류는 아니었다.

## 해결 방법

- 변경 파일: `backend/tests/test_e1_contract.py`
- 변경 내용: `PROJECT_FIELDS`에 `source_status`, `latest_analysis_status`를 추가해 문서화된 응답 계약과 일치시켰다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 없음: 응답에 서버 내부 `source_location`은 계속 포함하지 않는다.

```text
ruff check app tests
All checks passed!

pytest -q tests/test_e1_contract.py tests/test_project_resource_access.py tests/test_api_contract.py
36 passed, 4 warnings in 19.63s

pytest -q
214 passed, 5 warnings in 81.62s
```

## 남은 위험과 후속 작업

- 남은 문제: 없음
- 후속 작업: 프로젝트 응답 필드를 추가·삭제할 때 API 계약과 E1 계약 테스트를 함께 갱신한다.
- 관련 문서 업데이트: `docs/api-contract.md`는 이미 계산 필드의 의미를 기록하고 있어 변경하지 않는다.

## 참고 자료

- 로그 경로: GitHub Actions PR #38 Backend test
- 화면 캡처: 없음
- 관련 커밋: 수정 후 기록
