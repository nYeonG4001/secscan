# E2 인증, 인가 및 프로젝트 접근 통제 작업 상세

E2는 로그인 여부를 확인하는 데서 끝나지 않고, 요청 시점에 사용자의 역할과 프로젝트 관계를 다시 검증한다. 같은 분석 ID나 결과 ID를 직접 요청해도 현재 프로젝트 접근권한이 없으면 자원 존재를 알 수 없어야 한다.

## 공통 결정

- 요구사항 해석: SFR-001부터 SFR-006, SEC-001부터 SEC-006은 로그인, 역할, 프로젝트 소속을 함께 검증하도록 요구한다.
- 고려한 대안: 라우터마다 권한 확인 코드를 작성하거나, 공통 접근 검증 의존성을 만든다.
- 선택: 공통 프로젝트 접근 검증 의존성을 만들고 프로젝트, 분석, Finding 조회 경로가 이를 사용한다.
- 선택 이유:
  - 안전성: 새 조회 API에서 관계 검증을 빠뜨려 발생하는 IDOR 위험을 줄인다.
  - 사용자 경험: 권한 해제 뒤 프로젝트는 즉시 목록과 직접 주소에서 사라진다.
  - 일정 또는 구현 난이도: 한 번 구현한 검증을 E3부터 E6의 프로젝트 하위 기능에도 재사용한다.
  - 향후 확장: Git 소스와 분석 엔진이 추가돼도 프로젝트 관계 검증 정책을 유지한다.
- 이번 에픽에서 제외: 모든 기기의 세션 강제 폐기, 유휴 시간 만료, 계정 활성 상태 변경 화면과 API.
- 기록 위치: ADR-008, ADR-009, ADR-010, ADR-013, ADR-014, `docs/api-contract.md`

## E2-11 마감 검증 증거 (2026-08-27)

- 상태: E2-01부터 E2-11까지 완료. 각 완료 조건은 아래 작업별 테스트와 전체 회귀로 확인했다.
- 백엔드: 전용 PostgreSQL 데이터베이스 `secscan_test`에서 `TEST_DATABASE_URL`, `SECRET_KEY`, `SESSION_COOKIE_SECURE=false`를 설정해 `.venv/bin/ruff check .`와 `.venv/bin/python -m pytest -q`를 실행했다. ruff는 통과했고, 전체 pytest 139개를 수집·성공 종료했다.
- 프론트엔드: `npm run lint`, `npm test`(15개), `npm run typecheck`, `npm run build`가 모두 통과했다.
- 공통: `git diff --check` 통과. Docker Compose는 사용하지 않았고, 검증용 컨테이너만 사용했다.
- 검증 환경 주의: 샌드박스 실행은 localhost 테스트 DB TCP 연결을 차단했으나, 동일 명령을 권한 상승 환경에서 재실행해 통과시켰다. 코드·DB 구성의 실패가 아니므로 별도 troubleshooting 항목은 만들지 않았다.

## E2-01 로그인 API와 인증 쿠키 발급

- 상태: 완료
- 요구사항 매핑: SFR-001, SFR-002, SEC-001, TST-001
- 결정과 근거: 이메일과 비밀번호로 내부 계정을 인증한다. JWT를 브라우저 저장소가 아닌 `HttpOnly` 세션 쿠키로 전달한다. 계정 식별자 결정은 ADR-010, 비활성 계정 정책은 ADR-013, 쿠키 인증은 ADR-014를 따른다.
- 완료 조건:
  - 활성 ADMIN과 USER가 로그인하면 세션 및 CSRF 쿠키가 발급된다.
  - 로그인 응답에 인증 토큰, 비밀번호, 비밀번호 해시, 활성 상태가 포함되지 않는다.
  - 없는 이메일, 틀린 비밀번호, 비활성 계정은 서로 구분되지 않는 일반 401로 거부된다.
- 테스트: `backend/tests/test_auth_api.py`
- 증거: `test_active_account_can_log_in`, `test_login_response_does_not_expose_authentication_secrets`, `test_login_sets_httponly_session_cookie_and_readable_csrf_cookie`, `test_session_cookie_secure_setting_changes_by_environment`, 일반 401·timing-safe 검증 테스트가 2026-08-27 전체 pytest에서 통과

## E2-02 토큰 검증, 만료와 현재 사용자 조회

- 상태: 완료
- 요구사항 매핑: SFR-002, SEC-002, TST-001
- 결정과 근거: 토큰은 최대 24시간 유효하다. 유휴 시간 만료는 후속 보안 고도화로 남긴다. 보호 API는 서명과 만료 시각뿐 아니라 DB의 `active=true` 상태도 확인한다.
- 완료 조건:
  - 누락, 변조, 만료, 잘못된 사용자 식별자의 세션은 일반 401로 거부된다.
  - 비활성화된 계정의 기존 세션은 다음 보호 API 요청부터 401로 거부된다.
  - `GET /auth/me`는 유효한 세션에서 이메일과 역할만 반환한다.
- 테스트: `backend/tests/test_auth_api.py`, `backend/tests/test_auth_authorization.py`
- 증거: `test_invalid_session_cookie_is_rejected`, `test_missing_session_cookie_is_rejected`, `test_existing_token_is_rejected_after_account_is_deactivated`, `test_auth_me_returns_only_email_and_role`, `test_logout_is_idempotent_and_clears_authentication_cookies`가 2026-08-27 전체 pytest에서 통과

## E2-03 역할 기반 관리자 기능 통제

- 상태: 완료
- 요구사항 매핑: SFR-003, SFR-004, SFR-005, SFR-008, SEC-003, SEC-004, TST-002
- 결정과 근거: ADMIN만 프로젝트 생성과 수정, 접근권한 관리, 소스 등록과 분석 실행, 카탈로그 등록과 수정을 할 수 있다. 인증된 USER가 프로젝트와 무관한 관리자 기능을 요청하면 403으로 거부한다.
- 완료 조건:
  - ADMIN은 관리자 API를 정상 호출한다.
  - USER와 인증되지 않은 요청은 모든 관리자 API에서 각각 403과 401을 받는다.
- 테스트: `backend/tests/test_auth_authorization.py`, `backend/tests/test_project_api.py`
- 증거: 관리자 API 전체의 ADMIN 2xx, USER 403, 미인증 401 및 CSRF 누락·불일치 403을 2026-08-27 전체 pytest에서 확인

## E2-04 프로젝트 목록과 상세 조회 범위

- 상태: 완료
- 요구사항 매핑: SFR-006, SEC-004, TST-003
- 결정과 근거: ADMIN은 모든 프로젝트를, USER는 현재 `ProjectAccess` 관계가 있는 프로젝트만 조회한다. `GET /projects/{project_id}`를 추가해 목록과 직접 주소 모두 같은 검증을 적용한다.
- 완료 조건:
  - USER 목록에는 권한이 있는 프로젝트만 포함된다.
  - 분석 이력이 없는 권한 프로젝트도 USER 목록에 포함된다.
  - 권한이 해제된 프로젝트는 USER 목록에서 즉시 사라진다.
- 테스트: `backend/tests/test_project_access_api.py`, `backend/tests/test_project_resource_access.py`
- 증거: ADMIN 전체 조회, USER의 현재 관계 기반 목록·상세 조회, 분석 이력 없는 프로젝트 조회와 해제 직후 목록 제외를 2026-08-27 전체 pytest에서 확인

## E2-05 공통 프로젝트 접근권한 검증

- 상태: 완료
- 요구사항 매핑: SFR-006, SEC-004, SEC-005, SEC-006, TST-003
- 결정과 근거: 권한 검사 코드를 각 라우터에 반복하지 않고 공통 의존성으로 만든다. ADMIN은 통과하고 USER는 DB의 `ProjectAccess` 관계가 있을 때만 통과한다. 비인가 프로젝트 자원은 ADR-008에 따라 404로 처리한다.
- 완료 조건:
  - 권한 없는 USER가 프로젝트 상세, 분석 이력, 분석 상세, 결과 목록, 결과 상세를 요청하면 모두 404를 받는다.
  - 존재하지 않는 자원과 권한 없는 자원이 같은 404 정책을 사용한다.
- 테스트: `backend/tests/test_project_resource_access.py`
- 증거: 프로젝트 상세·분석 목록/상세·Finding 목록/상세에 대한 부여 전 404, 부여 후 200, 해제 후 404와 없는 자원의 404를 2026-08-27 전체 pytest에서 확인

## E2-06 프로젝트 접근권한 부여 API

- 상태: 완료
- 요구사항 매핑: SFR-005, DAR-004, SEC-003, TST-002, TST-003
- 결정과 근거: 관리자는 화면의 이메일 입력으로 USER에게 권한을 부여한다. 내부 DB는 계속 `user_id` 관계를 저장한다. 사용자 목록이나 내부 ID 입력 화면은 만들지 않는다.
- 완료 조건:
  - ADMIN이 존재하는 USER 이메일에 프로젝트 접근권한을 부여할 수 있다.
  - 접근권한 생성과 목록 응답에 `user_id`와 `user_email`이 포함된다. 화면은 이메일을 표시하고 해제 요청에는 내부 사용자 ID를 사용한다.
  - ADMIN 계정에는 별도 프로젝트 권한을 부여하지 않는다.
  - 같은 USER에 중복 부여하면 409을 반환한다.
  - 없는 프로젝트 또는 이메일은 404, ADMIN 대상은 422로 거부한다.
- 테스트: `backend/tests/test_project_access_api.py`
- 증거: 이메일 기반 부여 및 `user_id`/`user_email` 응답, 없는 이메일·프로젝트 404, ADMIN 대상 422, 중복 409을 `test_project_access_api.py`로 확인

## E2-07 프로젝트 접근권한 해제 API

- 상태: 완료
- 요구사항 매핑: SFR-005, DAR-004, DAR-010, SEC-003, TST-002, TST-003
- 결정과 근거: `DELETE /projects/{project_id}/access/{user_id}`는 관계만 삭제한다. 프로젝트, 분석 이력, Finding은 보존한다.
- 완료 조건:
  - ADMIN이 부여된 USER의 접근권한을 해제할 수 있다.
  - 존재하지 않는 프로젝트 접근 관계 해제는 404를 반환한다.
  - 권한 해제 뒤 해당 USER의 목록과 직접 프로젝트 하위 조회가 모두 차단된다.
- 테스트: `backend/tests/test_project_access_api.py`, `backend/tests/test_project_resource_access.py`
- 증거: ADMIN 204, 없는 관계 404, USER 403, 미인증 401 및 관계만 삭제돼 Project·Analysis·Finding 행이 남는 동작을 2026-08-27 전체 pytest에서 확인

## E2-08 분석과 Finding 직접 조회의 소속 검증

- 상태: 완료
- 요구사항 매핑: SEC-005, SEC-006, TST-003
- 결정과 근거: `analysis_id`와 `finding_id`는 URL에서 직접 받을 수 있으므로, 각 행이 속한 프로젝트까지 조회한 뒤 E2-05의 공통 검증을 적용한다.
- 완료 조건:
  - 권한 있는 USER는 자신의 프로젝트 분석과 결과를 조회한다.
  - 다른 프로젝트의 분석 ID와 Finding ID를 추측해도 404만 반환한다.
  - 결과 목록의 `analysis_id` 경로도 같은 검증을 적용한다.
- 테스트: `backend/tests/test_project_resource_access.py`
- 증거: `test_user_only_reads_currently_granted_project_resources_and_not_ids`와 `test_missing_project_analysis_and_finding_all_return_404`가 교차 프로젝트 IDOR과 없는 ID의 동일 404를 확인

## E2-09 역할별 분석과 결과 응답 재검증

- 상태: 완료
- 요구사항 매핑: SEC-003, SEC-004, SEC-009, TST-002, TST-007
- 결정과 근거: E1에서 역할별 Pydantic 응답 모델을 만들었다. E2에서는 접근 검증 후에도 ADMIN과 USER 응답의 필드 경계가 유지되는지 통합 테스트로 확인한다.
- 완료 조건:
  - USER 응답에 `error_code`, `error_message`, 실행 로그, `raw_result`, 서버 내부 저장 위치가 없다.
  - ADMIN 응답에는 계약상 허용된 상세 오류와 원본 결과가 포함된다.
- 테스트: `backend/tests/test_api_contract.py`, `backend/tests/test_project_resource_access.py`
- 증거: `test_api_contract.py`와 `test_allowed_user_response_keeps_sensitive_fields_hidden_after_access_check`가 USER의 내부 오류·실행 로그·`raw_result`·`source_snapshot_location` 미노출과 ADMIN의 허용 필드를 비교 확인

## E2-10 프론트 보호 라우트와 역할별 행동

- 상태: 완료
- 요구사항 매핑: SFR-001, SFR-003, SFR-005, SFR-006, SEC-004, TST-001, TST-002
- 결정과 근거: ADMIN과 USER는 같은 프로젝트 및 진단 기준 메뉴를 사용한다. ADMIN 전용 행동만 조건부로 렌더링하며, 실제 차단은 백엔드 권한 검증이 담당한다.
- 완료 조건:
  - 인증되지 않은 사용자는 보호 화면에서 로그인으로 이동한다.
  - 앱 시작과 새로고침 때 `/auth/me`으로 현재 역할을 확인한다.
  - ADMIN과 USER는 로그인 뒤 모두 프로젝트 목록으로 이동한다.
  - USER에게 프로젝트 생성, 접근권한 관리, 소스 등록 및 분석 실행 행동을 렌더링하지 않는다.
  - 401은 로그인 화면의 일반 안내, 403은 관리자 전용 안내, 404는 자원 존재를 드러내지 않는 일반 안내로 표시한다.
- 테스트: `frontend/src/App.test.tsx`, `frontend/src/pages/LoginPage.test.tsx`
- 증거: `/auth/me` 성공·401·5xx 재시도, 두 역할의 로그인 뒤 `/projects` 이동, USER의 관리자 행동 비노출, ADMIN 접근권한 Drawer, 401/403/404 일반 안내 및 브라우저 저장소 미사용을 2026-08-27 Vitest 15개로 확인

## E2-11 인증과 권한 거부 테스트

- 상태: 완료
- 요구사항 매핑: SEC-001, SEC-002, SEC-003, SEC-004, SEC-005, SEC-006, TST-001, TST-002, TST-003
- 결정과 근거: 보안 기능은 성공 시나리오만으로 완료되지 않는다. 허용과 거부를 같은 URL과 데이터로 짝지어 검증한다.
- 완료 조건:
  - 권한 부여 전 404, 부여 후 200, 해제 후 404를 프로젝트 상세, 분석, Finding 경로에서 확인한다.
  - USER의 관리자 API 요청은 403, 토큰 없음과 만료 토큰은 401을 확인한다.
  - CSRF 토큰이 없거나 틀린 쓰기 요청은 거부된다.
- 테스트: `backend/tests/test_auth_api.py`, `backend/tests/test_auth_authorization.py`, `backend/tests/test_project_api.py`, `backend/tests/test_project_access_api.py`, `backend/tests/test_project_resource_access.py`, `backend/tests/test_api_contract.py`, `frontend/src/App.test.tsx`, `frontend/src/pages/LoginPage.test.tsx`
- 증거: E2-11 마감 검증 증거 절의 백엔드 전체 pytest·프론트 Vitest 실행 결과와 각 역할별 허용·거부 응답 테스트
