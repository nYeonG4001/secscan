# E3 소스 등록과 업로드 보안 작업 상세

E3는 관리자만 ZIP 소스를 등록할 수 있게 하고, 신뢰할 수 없는 압축 파일이 서버 작업영역이나 이후 분석 실행에 영향을 주지 못하게 한다. E2의 쿠키 인증, 관리자 권한, 프로젝트 접근 검증을 그대로 사용한다.

## 공통 결정

- MVP 소스 등록 방식은 ZIP 파일 업로드만 지원한다. Git 저장소와 기관 내부 경로는 ADR-006에 따라 후속 범위다.
- 새 관리자 쓰기 API는 `require_admin`과 `require_csrf`를 함께 사용한다.
- 프로젝트 하위 자원은 E2의 공통 프로젝트 접근 검증을 재사용한다.
- 업로드 화면은 `ActionDrawer`를 재사용하고 USER에게 렌더링하지 않는다.

## MVP 선택과 보류

| 주제 | MVP 선택 | 보류한 확장 | 판단 이유 |
|---|---|---|---|
| 프로젝트 소스 관리 | 최신 소스 하나를 교체하고 분석마다 스냅샷 보존 | 업로드 버전 이력, 현재 버전 선택, 이전 버전 재분석과 비교 | 분석 결과 재현성은 스냅샷으로 보장한다. 버전 관리에는 새 데이터 모델, API, UI, 저장 용량 정책이 필요하므로 업로드 보안과 분석 실행을 우선한다. |

## E3-03 업로드 파일 자원 제한

- 상태: 완료
- 요구사항 매핑: SFR-007, SEC-007, SEC-008
- 결정과 근거: 원본 ZIP 크기만 제한하면 압축 해제 뒤의 자원 고갈을 막을 수 없다. ZIP 원본 25 MB, 실제 압축 해제 누적 100 MB, 최대 5,000개 파일, 개별 파일 10 MB를 제한한다. ZIP 항목별 압축 비율은 스트리밍 실측값으로 계산하고 실제 출력이 1 MB 이상일 때만 20:1 제한을 적용한다. 실제 압축 해제 크기 제한은 비율과 별도로 적용한다. 자세한 근거는 ADR-015를 따른다.
- 완료 조건:
  - ZIP 원본, 실제 압축 해제 누적 크기, 파일 수, 개별 파일 크기가 모두 제한된다.
  - ZIP 항목별 압축 비율은 실제로 소비한 압축 입력과 실제 압축 해제 출력으로 계산하며, 실제 출력 1 MB 이상부터 20:1 제한을 적용한다.
  - ZIP 메타데이터만 신뢰하지 않고 실제 압축 해제 중 누적값으로 제한을 다시 확인한다.
  - 제한 초과 시 처리 중단 뒤 생성된 작업영역과 임시 파일을 정리한다.
- 테스트: `backend/tests/test_source_archive.py`
- 증거: 2026-08-28: 제한 초과와 최소 출력 크기 전후 압축 비율 경계를 포함한 기반 테스트를 확인

## E3-01 소스 업로드 API와 활성 분석 상태

- 상태: 완료
- 요구사항 매핑: SFR-007, SFR-008, SFR-015, SEC-003, SEC-007
- 결정과 근거: 현재 소스 하나를 교체하는 `PUT /api/projects/{project_id}/source`에 ZIP 하나를 `multipart/form-data`로 보낸다. 소스 업로드와 분석 실행은 별도 행동이다. `PENDING` 또는 `RUNNING` 분석이 있으면 새 ZIP 업로드를 409으로 거부하고, `COMPLETED` 또는 `FAILED` 뒤에만 현재 프로젝트 소스를 교체한다. 같은 프로젝트의 동시 업로드도 `UPLOAD_IN_PROGRESS` 코드와 409으로 거부한다. 업로드 예약 대기열은 MVP에서 제공하지 않는다. 성공 응답과 안전한 오류 코드는 `docs/api-contract.md`, ADR-019, ADR-020, ADR-021을 따른다.
- 완료 조건:
  - ADMIN과 유효한 CSRF 요청만 ZIP 업로드를 시작할 수 있다.
  - 진행 중 분석이 있는 프로젝트의 업로드는 409으로 거부된다.
  - 새 ZIP 업로드는 분석을 자동 실행하지 않는다.
  - `source_status`는 저장 필드가 아니라 `source_location` 존재 여부로 계산한다. 성공 응답은 `project_id`, `source_status`, `target_languages`를 포함하고 서버 내부 경로와 파일명은 제외한다.
  - 오류 응답은 `ANALYSIS_ACTIVE`, `UPLOAD_IN_PROGRESS`, `ARCHIVE_TOO_LARGE`, `ARCHIVE_LIMIT_EXCEEDED`, `UNSAFE_ARCHIVE`, `NO_SUPPORTED_SOURCE`의 안정적인 코드를 사용한다.
- 테스트: `backend/tests/test_source_upload_api.py`
- 증거: 2026-08-28: ADMIN, USER, CSRF, 활성 분석, 동시 업로드, 분석 미생성 시나리오를 API 테스트로 확인

## E3-07 업로드 상태, 실패와 재시도 화면

- 상태: 완료
- 요구사항 매핑: SFR-007, SFR-015, SEC-007, SEC-008
- 결정과 근거: 내부 예외와 원본 경로를 노출하지 않고, 사용자가 취할 행동이 다른 오류 범주만 짧게 표시한다. 자동 재시도 대신 사용자가 명시적으로 다시 시도하며, 업로드 중에는 진행률과 취소를 제공한다. 자세한 문구와 근거는 ADR-020을 따른다.
- 완료 조건:
  - ADMIN은 파일 선택, 업로드 중 진행률, 취소, 실패, 성공 상태를 구분해 본다.
  - 오류 문구는 내부 경로나 서버 예외를 포함하지 않는다.
  - 취소와 실패 뒤 임시 ZIP 및 작업영역이 남지 않는다.
  - 취소 뒤에는 프로젝트 상태를 다시 조회해 현재 소스 교체 여부를 확인한다.
  - USER에게 소스 등록 Drawer와 업로드 상태가 렌더링되지 않는다.
- 테스트: `frontend/src/pages/SourceUploadDrawer.test.tsx`, `backend/tests/test_source_upload_api.py`
- 증거: 2026-08-28: 오류 범주별 안전한 문구, 취소 뒤 상태 갱신, USER 비노출을 프론트와 API 테스트로 확인

## E3-08 업로드 보안과 화면 테스트

- 상태: 완료
- 요구사항 매핑: SFR-007, SFR-011, SFR-015, SEC-003, SEC-007, SEC-008, TST-004
- 결정과 근거: 업로드 보안은 정상 ZIP의 성공만으로 검증할 수 없다. 같은 프로젝트에 대해 허용 ZIP, 제한 초과 ZIP, 경로 조작 ZIP, 권한 없는 요청을 짝지어 확인하고, 거부 뒤 현재 소스와 임시 작업영역이 안전한지 검증한다.

| 영역 | 허용 또는 정상 시나리오 | 거부 또는 경계 시나리오 | 테스트 파일 |
|---|---|---|---|
| 인증과 권한 | ADMIN과 유효 CSRF가 ZIP을 등록 | 미인증 401, USER 403, CSRF 누락 또는 불일치 403, 없는 프로젝트 404 | `backend/tests/test_source_upload_api.py` |
| 정상 업로드 | Java, JavaScript, Python 단일 언어와 복수 언어 ZIP 등록, 감지 언어 기록, 분석 미자동 실행 | 없음 | `backend/tests/test_source_upload_api.py`, `backend/tests/test_source_archive.py` |
| 자원 제한 | 제한 안의 ZIP 등록 | 원본 크기, 실제 압축 해제 누적 크기, 파일 수, 개별 파일 크기, 압축 비율 초과 | `backend/tests/test_source_archive.py` |
| ZIP 구조 | 안전한 상대 경로 ZIP 등록 | ZIP Slip, 절대 경로, Windows 또는 UNC 경로, NUL 문자, 문자 단위 중복 경로, 대소문자만 다른 경로, 심볼릭 링크, 하드 링크 | `backend/tests/test_source_archive.py` |
| 언어 감지 | 설정 파일과 문서를 포함한 지원 언어 소스 ZIP 등록 | 지원 소스 부재, TypeScript만 포함, 중첩 ZIP만 포함 | `backend/tests/test_source_archive.py` |
| 작업영역 | 새 내부 소스 경로 생성 뒤 DB commit으로 현재 `source_location` 갱신, 서버 시작 시 오래된 임시 및 비참조 소스 경로 정리 | DB commit 실패 뒤 새 소스 경로 정리, 이전 소스 유예 보존, API 응답에 내부 경로 미노출, 다른 프로젝트 경로 접근 불가 | `backend/tests/test_source_workspace.py`, `backend/tests/test_source_upload_api.py` |
| 활성 분석과 동시 업로드 | `COMPLETED`, `FAILED` 뒤 새 소스 등록 | `PENDING`, `RUNNING` 중 업로드 409과 `ANALYSIS_ACTIVE`, 첫 업로드 진행 중 두 번째 요청 409과 `UPLOAD_IN_PROGRESS`, 두 번째 요청의 임시 경로 미생성 | `backend/tests/test_source_upload_api.py`, `backend/tests/test_source_workspace.py` |
| 오류 응답 | 성공 응답에 감지 언어와 등록 상태만 포함 | 오류 응답에 안정적인 `code`만 포함하고 내부 경로와 원본 ZIP 항목명 미노출 | `backend/tests/test_source_upload_api.py`, `backend/tests/test_source_archive.py` |
| 프론트 Drawer | ADMIN 파일 선택, 진행률, 성공, 수동 재시도, 취소 뒤 상태 갱신 | USER 비노출, 오류 코드별 짧은 문구, 취소와 실패 뒤 업로드 상태 정리 | `frontend/src/pages/SourceUploadDrawer.test.tsx` |

- 자원 제한 테스트는 25 MB, 100 MB 같은 운영 기본값을 실제로 채우지 않는다. 테스트 전용 설정에서 더 작은 제한값을 주입해 같은 경계 동작을 빠르게 검증한다.
- 보안 거부 테스트는 HTTP 상태만 확인하지 않는다. 거부 뒤 임시 작업영역이 없고 DB의 기존 `source_location`이 바뀌지 않았는지 함께 확인한다.
- 증거: E3 구현 PR의 전체 백엔드, 프론트 테스트 로그와 각 보안 거부 응답

## E3-04, E3-05 ZIP 경로와 링크 검증

- 상태: 완료
- 요구사항 매핑: SFR-007, SEC-007, SEC-008
- 결정과 근거: ZIP은 경로 조작과 링크를 통해 작업영역 밖 파일에 접근할 수 있다. 모든 항목을 압축 해제 전에 검사하고, 절대 경로, 상위 경로 이동, Windows 경로, NUL 문자, 문자 단위 중복 경로, 대소문자만 다른 경로, 심볼릭 링크와 하드 링크를 포함한 ZIP 전체를 거부한다. 저장 위치의 파일시스템 특성이 아직 확정되지 않았으므로 경로 자동 수정이나 링크 허용과 함께 대소문자 구분 허용도 선택하지 않는다. 자세한 근거는 ADR-016을 따른다.
- 완료 조건:
  - 모든 ZIP 항목은 파일 생성 전에 검증된다.
  - 허용된 항목의 해석 경로가 작업영역 내부인지 다시 확인한다.
  - 위험 항목이 하나라도 있으면 ZIP 전체를 거부하고 작업영역에 파일을 남기지 않는다. 문자 단위 중복 경로와 대소문자만 다른 경로는 각각 전체 거부 대상이다.
  - 사용자 응답은 위험한 원본 경로를 포함하지 않는다.
- 테스트: `backend/tests/test_source_archive.py`
- 증거: 2026-08-28: 위험 경로, 링크, NUL 문자, 중복 경로를 압축 해제 전 전체 거부하고 staging 정리를 확인

## E3-02 프로젝트와 분석 작업영역 분리

- 상태: 완료
- 요구사항 매핑: SFR-007, SEC-007, SEC-008
- 결정과 근거: 프로젝트의 현재 소스와 분석이 사용한 소스는 수명 주기가 다르다. 새 업로드가 과거 분석의 근거를 바꾸지 않도록 성공한 ZIP은 새 내부 소스 경로에 보관하고, DB transaction의 `source_location` 갱신으로 현재 소스를 원자적으로 바꾼다. 이전 내부 소스는 즉시 삭제하지 않고 유예 기간 뒤 정리한다. E4는 분석 생성 시 DB의 현재 소스를 분석별 스냅샷으로 복사한다. 자세한 근거는 ADR-017을 따른다.
- 완료 조건:
  - 사용자 입력 경로가 아닌 서버 관리 경로에 성공한 업로드별 내부 소스가 저장된다.
  - 검증 중인 ZIP은 무작위 임시 경로에서만 처리된다.
  - 새 내부 소스 경로 생성 뒤 DB transaction의 `source_location` commit이 현재 소스 변경의 유일한 원자성 경계다.
  - DB commit 실패 뒤 새 내부 소스 경로와 요청 종료 시 실패한 임시 경로는 남지 않는다.
  - 서버 시작 시 기본 24시간보다 오래된 임시 경로와 현재 `source_location`에 참조되지 않는 내부 소스 경로를 정리한다.
  - E4는 이 현재 소스 경로를 분석별 스냅샷으로 복사한다. 실제 스냅샷 생성은 E4 범위다.
  - 프로젝트 현재 소스와 분석 스냅샷 경로는 API 응답에 포함되지 않는다.
- 테스트: `backend/tests/test_source_workspace.py`, `backend/tests/test_source_upload_api.py`
- 증거: 2026-08-28: DB commit 실패 뒤 새 내부 소스 경로 정리, 유예 기간 뒤 비참조 이전 소스 경로 정리, 내부 경로 미노출 확인

## E3-06 지원 소스 파일과 자동 언어 감지

- 상태: 완료
- 요구사항 매핑: SFR-004, SFR-007, SFR-011, DAR-003, TST-004, SEC-008
- 결정과 근거: 설정 파일과 문서를 포함한 정상 프로젝트 구조는 보존하되, Java `.java`, JavaScript `.js`·`.jsx`·`.mjs`·`.cjs`, Python `.py` 정규 파일만 언어 감지와 분석 후보로 사용한다. 언어 선택은 사용자 입력이 아니라 시스템 자동 감지 결과다. TypeScript는 핵심 MVP가 완료된 뒤 시간이 남을 때만 추가하는 선택 작업이다. 자세한 근거는 ADR-018을 따른다.
- 완료 조건:
  - 지원 소스 확장자를 통해 하나 이상의 언어가 자동 감지돼 프로젝트에 기록된다.
  - Java, JavaScript, Python 소스가 섞인 ZIP은 복수 언어를 감지한다.
  - 지원 소스 파일이 없는 ZIP은 저장 전에 거부한다.
  - 설정, 문서, 이미지, 바이너리, 중첩 ZIP은 자동 분석 후보가 아니다.
  - E4가 의존성 및 생성 결과물 디렉터리를 제외한 지원 소스 파일만 분석 입력으로 사용한다.
- 테스트: `backend/tests/test_source_archive.py`, `backend/tests/test_source_upload_api.py`
- 증거: 2026-08-28: 단일 언어와 복수 언어 ZIP의 `target_languages`, 지원 소스 부재 ZIP의 거부 응답을 확인. 실제 분석 입력 검증은 E4 범위다.
