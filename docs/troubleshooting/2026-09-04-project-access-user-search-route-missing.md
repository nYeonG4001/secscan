# Troubleshooting: 프로젝트 접근권한 사용자 검색 API 누락

## 기본 정보

- 작성일: 2026-09-04
- 작성자: Claude (design/review agent)
- 관련 에픽: E2 인증과 권한
- 관련 요구사항: 프로젝트 접근권한 부여 흐름 (사용자 이메일 검색 단계)
- 관련 PR 또는 커밋: 수정 후 기록
- 환경: 로컬 (정적 계약 감사 + 실제 백엔드 기동 확인)

## 문제 요약

프론트엔드는 접근권한 부여 전 사용자 확인을 위해 `GET /projects/{project_id}/access/user?email=...`을 호출하지만, 백엔드에는 이 경로에 대한 GET 라우트가 없어 관리자 화면의 권한 부여 흐름이 항상 실패했다.

## 증상

프론트엔드 단위 테스트는 `api.get`을 모킹하기 때문에 이 계약 불일치를 잡아내지 못했고, 실제 백엔드 기동 시에만 드러났다.

```text
GET /projects/2/access/user?email=user%40secscan.io → 405 Method Not Allowed
```

## 재현 방법

1. 관리자로 로그인한 뒤 프로젝트 상세 화면의 "프로젝트 관리" 패널을 연다.
2. 사용자 접근권한 부여 폼에 이메일을 입력하고 "검색"을 누른다.
3. `frontend/src/pages/ProjectDetailPage.tsx`의 `searchAccessUser()`가 `GET /projects/{project_id}/access/user`를 호출하지만, `backend/app/routers/projects.py`에는 `GET /{project_id}/access`(목록)와 `POST /{project_id}/access`(부여)만 존재해 405가 반환된다.

## 기대 결과

관리자가 이메일로 사용자를 검색하면 해당 사용자의 `user_id`, `user_email`, 프로젝트에 대한 `already_granted` 여부를 받아 확인 후 권한을 부여할 수 있어야 한다.

## 실제 결과

일치하는 라우트가 없어 405가 반환되고, `searchAccessUser()`의 에러 처리 분기 중 어느 상태 코드와도 일치하지 않아 "사용자를 검색하지 못했습니다. 다시 시도해 주세요."로 항상 실패했다.

## 원인 분석

- 확인한 증거: `backend/app/routers/projects.py`의 기존 라우트 목록(`list_projects`, `get_project`, `create_project`, `update_project`, `grant_access`, `list_access`, `revoke_access`, `upload_source`, `preflight_source`)에 `GET /{project_id}/access/user`가 없음. `frontend/src/pages/ProjectDetailPage.tsx:249`는 이 경로를 호출함.
- 원인: 프론트엔드 검색 UI(및 대응 에러 처리 분기)는 구현되었지만, 대응하는 백엔드 GET 라우트와 응답 스키마가 추가되지 않았다.
- 원인이 아니었던 가설: 인증/CSRF 설정 문제가 아니다 — 같은 프리픽스의 다른 `/access` 라우트는 정상 동작한다. 권한 정책(관리자 전용) 문제도 아니다.

## 해결 방법

- 변경 파일:
  - `backend/app/schemas/project.py`: `ProjectAccessUserSearchOut` 스키마 추가 (`user_id`, `user_email`, `already_granted`).
  - `backend/app/routers/projects.py`: `GET /{project_id}/access/user` 라우트 추가. `require_admin` 의존성 사용, CSRF는 요구하지 않음(읽기 전용 GET). 프로젝트 미존재/사용자 미존재 시 기존 컨벤션과 동일하게 404를 반환.
  - `backend/tests/test_project_access_api.py`: 정상 조회(미부여/기부여), 사용자 미존재 404, 프로젝트 미존재 404, 미인증 401, 일반 사용자 403 테스트 추가.
- 변경 내용: 프론트엔드가 이미 기대하고 있던 계약(`user_id`, `user_email`, `already_granted`)을 그대로 구현했다. 기존 `POST` 부여, `GET` 목록, `DELETE` 해제 동작은 변경하지 않았다.

## 검증

- [ ] 같은 재현 절차로 문제가 해결됨 (실제 백엔드 기동 후 재확인 필요 — 이번 작업에서는 Docker/DB를 새로 기동하지 않았다)
- [ ] 관련 단위 테스트 통과 (로컬에 PostgreSQL 기반 `TEST_DATABASE_URL`이 구성되어 있지 않아 미실행 — 아래 정적 검증만 수행)
- [ ] 관련 통합 또는 화면 테스트 통과 (프론트엔드 코드는 변경하지 않았으므로 해당 없음)
- [x] 기존 기능 회귀 없음 (diff는 새 라우트/스키마/테스트/문서 추가로 한정됨을 확인)
- [x] 보안 영향 확인: 신규 라우트도 `require_admin`으로 관리자만 접근 가능하며, 다른 프로젝트의 접근권한 여부는 노출하지 않는다(요청한 `project_id`에 한정해 `already_granted` 계산).

```text
cd backend
ruff check app/routers/projects.py app/schemas/project.py tests/test_project_access_api.py tests/test_source_upload_api.py
All checks passed!

git diff --check
(출력 없음, 공백 오류 없음)

python3 -c "import ast; [ast.parse(open(f).read()) for f in [...]]"
OK (구문 오류 없음)
```

## 남은 위험과 후속 작업

- 남은 문제: 로컬에 PostgreSQL 테스트 DB가 없어 `pytest`로 신규/기존 테스트를 실행하지 못했다. 다음 작업자는 `TEST_DATABASE_URL`이 설정된 환경에서 `pytest backend/tests/test_project_access_api.py`를 실행해 실제 통과 여부를 확인해야 한다.
- 후속 작업: 실제 통합 환경에서 관리자 화면의 이메일 검색 → 확인 다이얼로그 → 권한 부여 흐름을 수동으로 재확인한다.
- 관련 문서 업데이트: 없음 (API 계약 문서에 이미 이 흐름이 전제되어 있었고, 이번 변경은 누락된 구현을 채운 것).

## 참고 자료

- 로그 경로: 없음
- 화면 캡처: 없음
- 관련 커밋: 수정 후 기록
