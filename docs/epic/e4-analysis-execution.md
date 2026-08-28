# E4 정적 분석 실행 작업 상세

E4는 E3에서 안전하게 등록한 현재 프로젝트 소스를 분석별 스냅샷으로 복사하고, Semgrep 실행과 분석 상태 전환을 관리한다. 분석 실행은 관리자만 시작할 수 있고, 일반 사용자는 권한 있는 프로젝트의 상태와 결과만 조회한다.

## E4-01, E4-03, E4-04 분석 실행기와 상태 전환

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-008, SFR-015, DAR-005, DAR-008, SEC-009
- 결정과 근거: 앱 내부 `ThreadPoolExecutor(max_workers=1)`가 분석을 하나씩 실행한다. 관리자 요청은 E3 업로드 잠금을 짧게 확인한 뒤 분석 행을 `PENDING`으로 저장하고 즉시 응답한다. 실행 작업은 요청 DB 세션을 재사용하지 않고 별도 세션에서 스냅샷 복사와 Semgrep 실행을 처리한다. 단일 실행기는 서로 다른 프로젝트의 Semgrep 프로세스가 무제한으로 생성되는 것을 막는다. 자세한 근거는 ADR-022, ADR-024를 따른다.
- 완료 조건:
  - 관리자 분석 요청은 새 `PENDING` 분석 이력을 만들고 즉시 응답한다.
  - 실행기는 `PENDING → RUNNING → COMPLETED` 또는 `FAILED` 상태 전환만 수행한다.
  - 업로드가 진행 중이면 분석 요청은 `409 SOURCE_UPLOAD_IN_PROGRESS`로 거부된다. 업로드 잠금 확인과 `PENDING` 저장은 같은 프로젝트 잠금 안에서 처리한다.
  - `PENDING` 저장 시 `source_location`, `target_languages`, `analyses/{analysis_id}/source` 스냅샷 위치를 확정한다. `RUNNING` 작업이 현재 소스 전체를 실제 스냅샷 위치로 복사한다.
  - Semgrep은 스냅샷의 Java, JavaScript, Python 정규 파일만 분석하며 의존성·생성 결과 디렉터리와 TypeScript를 제외한다.
  - 서버 시작 시 남은 `PENDING` 또는 `RUNNING` 분석은 `FAILED`로 전환한다.
  - 재실행은 기존 분석 행을 수정하지 않고 새 분석 행을 만든다.
- 테스트: E4-09에서 분석 생성 즉시 응답, 상태 전환, 재시작 복구, 프로젝트별 활성 분석 제한을 검증한다.

## E4-02 고정 Semgrep 보안 규칙과 언어 연결

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-008, SFR-010, SFR-011, DAR-005, TST-005, QLT-003, SEC-010
- 결정과 근거: 백엔드 이미지에 포함한 고정 버전 Semgrep OSS CLI와 공식 `p/security-audit` 규칙 팩의 저장소 고정본을 사용한다. 규칙 자동 선택과 원격 규칙 팩 직접 참조는 실행 시점에 `rule_id`가 달라져 KISA 매핑과 기대 결과를 흔들 수 있으므로 사용하지 않는다. 규칙 고정본의 출처와 라이선스는 `backend/semgrep-rules/THIRD_PARTY_NOTICES.md`에 기록한다. 자세한 근거는 ADR-023을 따른다.
- 완료 조건:
  - Semgrep CLI 버전과 실행 규칙 고정본이 분석 메타데이터에 기록된다.
  - Java, JavaScript, Python으로 감지된 소스만 Semgrep 분석 입력에 포함한다.
  - Semgrep 결과는 JSON으로 저장해 E5가 `rule_id`를 KISA 카탈로그와 연결할 수 있다.
  - 규칙 파일 변경은 별도 PR, 라이선스 확인, 영향받는 기대 결과 테스트 갱신을 거친다.
- 결정 필요: 고정할 Semgrep CLI 버전은 E4-01 구현 전에 호환성 검증 뒤 기록한다. Java의 추가 공식 규칙은 E5 매핑 결과를 근거로 판단한다.
- 테스트: E4-09에서 고정 규칙 파일을 사용한 Java, JavaScript, Python 샘플의 예상 `rule_id`를 검증한다.

## E4-05 실행 시간과 자원 제한

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-008, SFR-015, SEC-007, SEC-009, SEC-010
- 결정과 근거: Semgrep은 Docker socket 없이 백엔드 이미지의 고정 CLI를 subprocess로 실행한다. backend와 Semgrep은 전용 non-root 사용자로 실행하고, 런타임 저장소는 코드 bind mount와 분리된 `/var/lib/secscan/storage` named volume에 둔다. 별도 실행 래퍼가 Semgrep 실행 전에 1 GiB 주소 공간과 120초 CPU 시간을 제한한다. 부모 실행기는 120초 경과 시간 제한 뒤 프로세스 그룹 전체를 종료한다. backend 컨테이너 1.5 GiB 상한은 서비스 전체를 보호하는 2차 제한이다. 자세한 근거는 ADR-025를 따른다.
- 완료 조건:
  - `backend/app/core/config.py`의 `STORAGE_ROOT` 기본값이 `/var/lib/secscan/storage`다.
  - `backend/Dockerfile`이 전용 non-root 사용자를 생성하고 `/var/lib/secscan/storage`를 만들고 소유권을 부여한 뒤 `USER`를 지정한다.
  - `docker-compose.yml` backend가 `source_storage:/var/lib/secscan/storage` named volume과 `mem_limit: 1.5g`를 사용한다.
  - 개발 Compose에서 named volume 저장소의 업로드, 스냅샷 복사, 정리 작업이 정상 쓰기 권한으로 동작한다.
  - Semgrep은 `shell=False`와 인자 배열로 실행되며 `preexec_fn`을 사용하지 않는다.
  - 실행 래퍼가 `RLIMIT_AS=1 GiB`, `RLIMIT_CPU=120초`를 적용한다.
  - 경과 시간 120초가 지나면 `SIGTERM`, 유예 뒤 `SIGKILL`로 Semgrep 프로세스 그룹 전체를 종료한다.
  - backend Compose 컨테이너에는 1.5 GiB 메모리 상한이 적용된다.
  - timeout, CPU 또는 메모리 제한 실패는 일반 사용자에게 내부 정보를 노출하지 않고, 관리자에게만 상세 원인과 로그를 제공한다.
- 결정 필요: 강한 OS 수준 읽기 전용 격리가 필요한 배포에서는 Semgrep sidecar 또는 별도 실행 환경을 후속으로 검토한다.
- 테스트: E4-09에서 timeout 뒤 하위 프로세스가 남지 않는지, 자원 제한 오류 상태, non-root 실행, named volume 쓰기 권한을 검증한다.

## E4-06 실행 오류와 관리자용 로그

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-015, DAR-005, SEC-003, SEC-009
- 결정과 근거: `ANALYSIS.error_code`, `error_message`, 새 `execution_log`를 분리한다. 로그는 Semgrep 표준 오류와 실행 단계 정보의 최근 64 KiB만 보존한다. Semgrep을 스냅샷 디렉터리에서 상대 경로로 실행해 절대 경로가 처음부터 로그에 나타나지 않게 하며, 스크러빙은 보조 방어로만 사용한다. USER는 일반 실패 안내만, ADMIN은 오류 코드·상세 메시지·제한된 로그를 확인한다. 자세한 근거는 ADR-026을 따른다.
- 완료 조건:
  - timeout, 자원 제한, 스냅샷 실패, 엔진 비정상 종료, 잘못된 엔진 출력, 서버 중단을 안정적인 오류 코드로 구분한다.
  - `execution_log`는 64 KiB를 넘지 않고, `raw_result`와 분리해 저장한다.
  - USER 응답에는 `error_code`, `error_message`, `execution_log`, `raw_result`가 없다.
  - ADMIN 응답에만 안전하게 정리된 상세 오류와 `execution_log`가 있다.
  - Semgrep은 스냅샷 디렉터리를 작업 디렉터리로 사용하고 상대 경로만 인자로 전달한다.
  - 서버 내부 저장 경로, 실행 명령, 환경변수, 업로드 원본 파일명은 오류 응답과 `execution_log`에 없다.
- 결정 필요: 없음
- 테스트: E4-09에서 timeout과 잘못된 JSON 출력을 모의하고, 응답 전체와 `execution_log`에 저장 경로·업로드 원본 파일명이 없는지 확인한다.

## E4-07 중복 실행 방지와 재실행 처리

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-008, SFR-015, DAR-005, DAR-008
- 결정과 근거: 같은 프로젝트의 `PENDING` 또는 `RUNNING` 분석은 `409 ANALYSIS_ACTIVE`로 거부하고, 응답의 `analysis_id`, `status`로 화면을 진행 중 분석에 연결한다. 앱 수준 확인과 DB의 `uq_analyses_project_active` 제약을 함께 사용해 동시 요청도 차단한다. 완료 또는 실패한 분석의 다시 분석은 별도 API 없이 `POST /api/analyses`를 재호출하며, 언제나 요청 시점의 현재 소스로 새 분석 이력을 만든다. 자세한 근거는 ADR-027을 따른다.
- 완료 조건:
  - 같은 프로젝트에서 활성 분석 중 새 요청은 `409 ANALYSIS_ACTIVE`, `analysis_id`, `status`를 반환한다.
  - 동시 요청 경합으로 DB 제약이 충돌해도 같은 409 계약으로 응답한다.
  - 완료 또는 실패한 분석은 기존 행을 수정하지 않고 새 분석 행으로 다시 실행한다.
  - 다시 분석은 현재 프로젝트 소스를 사용하며, 과거 스냅샷 선택 재실행 API나 UI는 제공하지 않는다.
- 결정 필요: 없음
- 테스트: E4-09에서 이중 클릭, 동시 요청, 완료 후 재실행, 실패 후 재실행, 과거 분석 행 불변성을 검증한다.

## E4-08 분석 상태와 실행 화면 연결

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-008, SFR-015, SEC-003, SEC-009
- 결정과 근거: 분석 생성 성공 뒤 ADMIN은 분석 상세 경로로 이동한다. `PENDING`, `RUNNING` 상태는 3초 간격 폴링하고, 완료되면 같은 경로에서 결과 목록으로 전환한다. USER와 ADMIN 모두 권한 있는 상태를 보지만, 상세 오류와 로그는 ADMIN만 본다. 네트워크 오류는 분석 실패와 구분한다. 자세한 근거는 ADR-028을 따른다.
- 완료 조건:
  - 분석 생성 성공 뒤 ADMIN이 새 분석 상세 상태 화면으로 이동한다.
  - `PENDING`, `RUNNING` 상태에서만 3초 간격 폴링하고, 완료·실패·화면 이탈 때 중단한다.
  - `COMPLETED`는 결과 목록을, `FAILED`는 역할별 실패 안내를 같은 분석 상세 경로에서 표시한다.
  - USER는 일반 실패 안내만, ADMIN은 오류 코드·상세 메시지·제한 로그·현재 소스 재실행 행동을 본다.
  - `ANALYSIS_ACTIVE`는 기존 `analysis_id` 상태 화면으로 이동하고, `SOURCE_UPLOAD_IN_PROGRESS`는 `소스 업로드가 진행 중입니다. 완료 후 다시 시도해 주세요.` 안내를 표시한다.
  - 폴링의 네트워크 또는 5xx 오류는 분석 실패 상태로 바꾸지 않고 수동 새로고침을 제공한다.
- 결정 필요: 없음
- 테스트: E4-09에서 상태별 폴링 시작·중단, 완료 화면 전환, USER 상세 오류 미노출, 401·5xx 처리, 두 409 코드별 행동을 검증한다.

## E4-09 분석 처리 허용, 실패, 경계 시나리오 테스트

- 상태: 테스트 기준 확정, 구현 전
- 요구사항 매핑: SFR-008, SFR-010, SFR-011, SFR-015, DAR-005, DAR-008, SEC-003, SEC-007, SEC-009, SEC-010, TST-004, TST-005
- 결정과 근거: 실제 Semgrep 네트워크나 원격 규칙 레지스트리에 의존하지 않는 단위·API 테스트를 기본으로 한다. Semgrep 실행기는 고정 규칙과 테스트용 실행 파일을 주입해 명령 구성, 상태 전환, 제한, 오류 처리를 검증한다. 고정 이미지와 non-root 실행은 Docker 검증에서 별도로 확인한다.
- 완료 조건:
  - 분석 생성, 실행기 상태 전환, 재시작 중단 처리, 재실행이 새 행을 만드는 것을 검증한다.
  - Java, JavaScript, Python 대상 파일만 Semgrep 인자로 전달되고 제외 디렉터리·TypeScript·설정·문서는 전달되지 않음을 검증한다.
  - 고정 로컬 규칙 경로, `--json --quiet --oss-only`, `shell=False`, 상대 경로 작업 디렉터리, 실행 메타데이터 기록을 검증한다.
  - timeout에서 프로세스 그룹 종료, CPU·주소 공간 제한 래퍼, 1.5 GiB Compose 제한, non-root 이미지와 named volume 쓰기 권한을 검증한다.
  - `ANALYSIS_TIMEOUT`, `ANALYSIS_RESOURCE_LIMIT`, `SOURCE_SNAPSHOT_FAILED`, `ENGINE_EXECUTION_FAILED`, `ENGINE_OUTPUT_INVALID`, `ANALYSIS_INTERRUPTED` 상태와 관리자용 제한 로그를 검증한다.
  - USER 응답에 오류 코드·상세 메시지·실행 로그·원본 결과가 없고, ADMIN 응답에만 허용된 정보를 포함함을 검증한다.
  - 오류 응답과 `execution_log`에 저장 경로, 실행 명령, 환경변수, 업로드 원본 파일명이 없는지 검증한다.
  - ADMIN의 정상 요청, USER 403, 미인증 401, 권한 없는 프로젝트 404, 업로드 진행 중 409, 활성 분석 중복 409, 동시 요청 DB 경합을 검증한다.
  - 프론트에서 분석 생성 뒤 상태 화면 이동, `PENDING`·`RUNNING` 3초 폴링, 완료 결과 전환, 실패 역할 분기, 401·5xx 처리, 두 409 코드별 행동을 검증한다.
- 테스트 파일:
  - `backend/tests/test_analysis_execution.py`: 실행기, 상태 전환, 스냅샷, Semgrep 명령, 오류와 로그
  - `backend/tests/test_analysis_api.py`: 인증, 권한, 프로젝트 관계, 중복·업로드 경합 API 계약
  - `backend/tests/test_semgrep_runner.py`: timeout, 프로세스 그룹 종료, 자원 제한 래퍼, 잘못된 JSON
  - `frontend/src/pages/AnalysisStatusPage.test.tsx`: 상태 폴링과 역할별 실패 화면
  - `frontend/src/pages/ProjectDetailPage.test.tsx`: 분석 시작, 버튼 상태, 두 409 코드 처리
  - Docker 검증: 고정 Semgrep CLI 버전, non-root 사용자, named volume 저장소 쓰기 권한
- 증거: 관련 pytest·Vitest 실행 로그, Docker 이미지 실행 결과, ADMIN/USER 상태 화면 캡처 또는 수동 확인 기록

## 이후 작업

- 구현 전 남은 확인: 고정할 Semgrep CLI 버전과 규칙 고정본 revision을 호환성·라이선스 확인 뒤 `THIRD_PARTY_NOTICES.md`에 기록한다.
