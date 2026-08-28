# E5 결과 정규화와 KISA 매핑 작업 상세

E5는 E4가 저장한 Semgrep JSON 결과를 엔진 독립적인 진단 결과로 정규화하고, 가능한 결과를 KISA 카탈로그와 연결해 Finding으로 저장한다. 실제 Semgrep `check_id`와 규칙 고정본은 E4 구현 뒤 확인하며, 이 문서는 그 출력에 의존하지 않는 공통 구조와 보존 규칙부터 확정한다.

## E5-01, E5-02 외부 결과 파서와 공통 진단 결과 변환기

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-009, SFR-014, DAR-006, DAR-008, QLT-001, QLT-004
- 결정과 근거: Semgrep JSON을 DB나 API에 직접 연결하지 않는다. Semgrep 전용 파서가 공통 `NormalizedFinding`으로 변환하고, 저장 서비스가 이를 Finding과 KISA 매핑 결과로 바꾼다. `NormalizedFinding`은 `engine_rule_id`, `rule_name`, `severity`, `confidence`, `language`, 상대 `file_path`, 시작 `line`, 끝 `end_line`, `message`, `evidence`, `raw_result`를 가진다. `engine_rule_id`는 Semgrep `check_id`를 원문 그대로 담는 필수 값이며 Finding에도 `NOT NULL`로 저장한다. 같은 분석에서 같은 규칙과 코드 위치가 중복 저장되지 않도록 내부 `finding_fingerprint`을 만들고 `analysis_id`와 함께 고유하게 강제한다. 탐지 근거·조치 권고·코드 조각의 세부 구성은 E5-05와 ADR-033을 따른다. 자세한 근거는 ADR-029, ADR-035를 따른다.
- 완료 조건:
  - Semgrep 출력 구조는 파서 안에만 의존하고, 이후 저장·조회 계층은 `NormalizedFinding`만 사용한다.
  - 모든 저장 Finding은 비어 있지 않은 `engine_rule_id`와 사람이 읽는 `rule_name`을 가진다.
  - `engine_rule_id`는 Semgrep `check_id` 원문을 보존하며, `rule_name`과 KISA `kisa_code`를 대체하지 않는다.
  - `line`과 `end_line`은 엔진 결과의 시작·끝 줄을 보존하며, 코드 조각은 저장 서비스가 분석 시점 스냅샷에서 별도로 만든다.
  - `FINDING.engine_rule_id`와 `KISA_RULE_MAPPING.engine_rule_id`의 엔진별 동일 값이 E5-03 KISA 매핑 조회 기준이다.
  - 경로는 분석 스냅샷 기준 상대 경로만 저장하고 절대 서버 경로는 정규화 결과와 API에 포함하지 않는다.
  - `finding_fingerprint`은 `engine_rule_id`, 정규화한 상대 `file_path`, `line`, 유효 끝 줄을 NUL 구분자로 연결한 UTF-8 문자열의 SHA-256 값이며 API에 노출하지 않는다.
  - 유효 끝 줄은 `end_line`이 있으면 그 값, 없으면 `line`, `line`도 없으면 `NO_LINE` 표식이다. `(analysis_id, finding_fingerprint)` UNIQUE로 같은 분석 안의 중복 결과를 막는다.
  - 같은 분석에서 같은 지문이 다시 나오면 엔진 출력 순서상 첫 결과만 저장한다. 다른 분석 실행의 Finding은 서로 중복 제거하지 않는다.
- 결정 필요: E4의 고정 Semgrep 출력에서 표시명과 심각도·신뢰도 메타데이터 위치를 확인한 뒤, E5-03의 실제 매핑 데이터와 E5-04의 fixture를 확정한다.
- 테스트: E5-09에서 Java, JavaScript, Python의 고정 JSON fixture를 파싱해 필수 `engine_rule_id`, 명칭, 상대 경로와 원본 결과 보존을 검증한다. 같은 지문 중복의 단일 저장, `end_line` NULL의 지문 정규화, 서로 다른 필드 조합의 지문 분리를 검증한다.

## E5-03 KISA 항목 매핑 규칙

- 상태: 구조 결정 완료, 실제 규칙 목록 대기
- 요구사항 매핑: SFR-010, SFR-012, SFR-013, SFR-014, QLT-002, QLT-003, SEC-010
- 결정과 근거: `KISA_RULE_MAPPING`이 엔진 규칙과 KISA 항목을 연결한다. 한 KISA 항목에는 여러 언어·패턴 규칙을 연결할 수 있고, `UNIQUE(engine, engine_rule_id)`로 하나의 규칙이 여러 KISA 항목에 중복 연결되는 것을 막는다. 기존 `KISA_CATALOG.semgrep_rule_id`는 E5 migration에서 제거한다. 매핑은 API나 관리자 UI가 아닌 코드 리뷰 PR의 시드 또는 버전 관리 데이터로 관리한다. 자세한 근거는 ADR-030을 따른다.
- 완료 조건:
  - `KISA_RULE_MAPPING`에 `engine`, `engine_rule_id`, `kisa_code`와 복합 UNIQUE·외래키 제약이 있다.
  - KISA 항목 하나에 여러 Semgrep 규칙을 연결할 수 있다.
  - 동일한 `(engine, engine_rule_id)`는 두 KISA 항목에 연결되지 않는다.
  - `KISA_CATALOG.semgrep_rule_id`와 현재 이를 노출하는 `CatalogItemOut` 필드는 E5 migration에서 제거한다. 생성·수정 스키마에는 매핑 필드를 추가하지 않는다.
  - `/api/rule-mappings` 같은 매핑 관리 API는 만들지 않는다.
  - 고정 Semgrep CLI·규칙 출력 확인 뒤 실제 매핑 시드, 카탈로그 구현 상태, 언어별 기대 결과 테스트를 함께 갱신한다.
- 결정 필요: 실제 Semgrep `check_id`별 KISA 매핑 목록은 E4 구현 뒤 확정한다.
- 테스트: E5-09에서 다수 규칙의 동일 KISA 연결 허용, 동일 엔진 규칙의 다른 KISA 연결 거부, 매핑·미매핑 결과 저장을 검증한다.

## E5-04 미매핑 결과 보존과 역할별 노출

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-009, SFR-014, DAR-006, DAR-008, SEC-003, SEC-009, QLT-004
- 결정과 근거: 정규화에 성공한 엔진 결과는 KISA 매핑 여부와 관계없이 모두 Finding으로 저장한다. 미매핑 결과는 `kisa_code`, `criterion_id`, `recommendation`을 `NULL`로 두고, `engine_rule_id`, `rule_name`, 심각도, 신뢰도, 언어, 상대 파일 위치, 메시지, 탐지 근거, 원본 결과를 보존한다. 미매핑 결과를 KISA 카탈로그에 자동 추가하거나 카탈로그 구현 상태를 자동 변경하지 않는다. 매핑 추가는 E5-03의 코드 리뷰 PR 기반 매핑 데이터 갱신으로만 수행한다. 권한 있는 USER와 ADMIN 모두 매핑과 미매핑 결과를 조회하고 `engine_rule_id`를 확인할 수 있으며, `raw_result`는 ADMIN만 조회한다. 심각도는 매핑 결과면 분석 시점의 KISA `default_severity`를 복사하고, 미매핑 결과면 엔진 심각도를 공통 값으로 정규화한다. 신뢰도는 KISA 매핑과 무관하게 엔진 메타데이터만 정규화한다. 자세한 근거는 ADR-031, ADR-032를 따른다.
- 완료 조건:
  - 매핑 실패가 Finding 저장 실패로 이어지지 않는다.
  - 미매핑 Finding은 `kisa_code`, `criterion_id`, `recommendation`이 비어 있고, 엔진 규칙 식별자와 사용자용 진단 정보는 보존한다.
  - 목록과 상세 API는 권한 있는 USER와 ADMIN 모두 `KISA_MAPPED`, `UNMAPPED` 결과를 조회하고 필터링할 수 있다.
  - `engine_rule_id`는 두 역할의 Finding 응답에 포함하고, `raw_result`는 ADMIN 응답에만 포함한다.
  - 자동 카탈로그 생성, 자동 매핑, 매핑 관리 API는 만들지 않는다.
  - `Finding.severity`는 `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`만 저장하고, `Finding.confidence`는 `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`만 저장한다.
  - `KisaCatalog.default_severity`는 `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`만 저장한다.
- 결정 필요: E4의 고정 Semgrep 출력에서 실제 심각도 표기와 신뢰도 메타데이터 위치를 확인해 fixture를 확정한다. 지원하지 않는 표기는 안전하게 `UNKNOWN`으로 정규화한다.
- 테스트: E5-09에서 매핑 규칙이 없는 결과의 저장, USER와 ADMIN의 `engine_rule_id` 조회, USER 응답의 `raw_result` 미노출, UNMAPPED 필터, 심각도와 신뢰도 허용값 제약, 매핑과 미매핑 심각도 정규화를 검증한다.

## E5-05 탐지 근거, 코드 조각과 조치 권고

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-009, SFR-014, DAR-006, DAR-008, SEC-003, SEC-008, QLT-004
- 결정과 근거: `message`는 엔진이 제공한 짧은 진단 설명을 저장한다. `evidence`는 고정 Semgrep 출력에서 얻는 안전한 탐지 근거를 최대 2 KiB로 저장하며, 근거가 없으면 엔진 규칙 식별자와 상대 파일 범위를 이용한 짧은 대체 문구를 저장한다. `code_snippet`은 엔진 원본 출력에 의존하지 않고 분석 시점 소스 스냅샷에서 추출한다. 시작 `line`과 끝 `end_line` 전후 2줄을 포함하되 원본 코드 줄은 최대 20줄, 전체 텍스트는 최대 8 KiB로 제한한다. 범위가 길면 탐지 범위의 앞뒤를 남기고 생략 표식을 넣는다. 코드 조각은 전체 소스 뷰어가 아니며, 권한 있는 USER와 ADMIN의 Finding 응답에 포함한다. 자세한 근거는 ADR-033을 따른다.
- 완료 조건:
  - `line`은 시작 줄이며 `end_line`은 끝 줄이다. `end_line`은 NULL을 허용하지만 두 값이 있으면 `end_line >= line`만 저장된다.
  - Semgrep 결과의 시작·끝 줄을 각각 저장하고, 단일 줄 결과는 같은 값을 저장한다.
  - 코드 조각 추출 전 `snapshot_root / file_path`의 해석 경로가 분석 스냅샷 루트 안에 있는지 재검증한다.
  - 코드 조각은 상대 경로와 제한된 줄 범위만 사용하며, 서버 내부 경로, 전체 파일, 원본 ZIP 파일명은 포함하지 않는다.
  - 코드 조각을 만들 수 없어도 Finding 저장과 분석 완료는 실패하지 않으며, 이 경우 위치, 메시지, 탐지 근거와 조치 권고는 저장한다.
  - 매핑 결과의 `recommendation`은 정규화 시점 KISA 카탈로그 값을 복사하고, 미매핑 결과는 NULL로 둔다.
- 결정 필요: E4의 고정 Semgrep JSON에서 안전한 탐지 근거 후보 필드를 확인해 `evidence` 추출 fixture를 확정한다.
- 테스트: E5-09에서 단일 줄과 여러 줄 범위, `end_line < line` 거부, 스냅샷 루트 이탈 경로 거부, 코드 조각 줄·바이트 제한, 코드 조각 추출 실패 뒤 Finding 보존, USER와 ADMIN의 코드 조각 조회를 검증한다.

## E5-06 원본 결과와 분석 시점 보존

- 상태: 결정 완료, 구현 전
- 요구사항 매핑: SFR-014, DAR-006, DAR-008, DAR-009, SEC-003, SEC-009, QLT-004
- 결정과 근거: `Analysis.raw_result`에는 Semgrep 전체 `results[]`를 저장하지 않는다. 대신 엔진 이름과 버전, 규칙 고정본 식별자, 출력 형식 버전, 종료 상태, 결과 수처럼 안전한 실행 메타데이터만 저장한다. Finding 하나의 원본 Semgrep 결과 객체는 `Finding.raw_result`에만 저장하며 ADMIN만 조회한다. `Analysis.summary`는 사용자도 볼 수 있는 결과 집계용이고, `Analysis.raw_result`는 관리자용 실행 메타데이터이므로 역할이 다르다. 자세한 근거는 ADR-034를 따른다.
- 완료 조건:
  - 완료 분석의 `Analysis.raw_result`에는 Finding 목록 또는 원본 `results[]` 배열이 없다.
  - 각 저장 Finding은 자신을 만든 원본 결과 객체를 `raw_result`로 보존하며 USER 응답에는 포함하지 않는다.
  - Semgrep 결과 중 하나라도 파싱 또는 정규화할 수 없으면 분석은 `ENGINE_OUTPUT_INVALID`로 실패하고, 해당 분석의 Finding 저장은 하나도 남기지 않는다.
  - 정규화와 Finding 저장은 하나의 DB 트랜잭션으로 처리해 일부 결과만 남지 않는다.
  - 코드 조각 추출 실패처럼 ADR-033이 허용한 보조 정보 실패는 정규화 실패로 취급하지 않는다.
  - 서버 내부 경로, 실행 명령, 환경변수, 업로드 ZIP 원본 파일명은 어떤 `raw_result`에도 저장하지 않는다.
- 결정 필요: 없음
- 테스트: E5-09에서 다수 Finding의 개별 원본 결과 저장, Analysis 원본 결과의 `results[]` 미포함, 중간 정규화 실패 시 전체 롤백과 `ENGINE_OUTPUT_INVALID`, USER의 원본 결과 미노출을 검증한다.

## E5-09 언어별 취약 코드와 정상 코드 테스트

- 상태: 테스트 원칙 결정 완료, 실제 fixture 대기
- 요구사항 매핑: SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
- 결정과 근거: Java, JavaScript, Python은 모두 MVP 지원 언어로 유지한다. E4가 고정한 Semgrep CLI와 벤더링 규칙을 실제 실행해 언어별 지원 규칙을 확인한 뒤, 각 언어에서 KISA 매핑 취약 코드와 같은 규칙이 탐지되지 않아야 하는 정상 코드를 최소 하나씩 만든다. 실제 샘플은 KISA 매핑의 명확성, 다언어 지원 여부, 취약·정상 차이의 설명 가능성, 재현 안정성 순으로 늘린다. 고정 탐지 항목 수는 정하지 않고 검증 가능한 항목을 최대한 추가한다. TypeScript는 확장 구조만 유지하고 후순위로 둔다. 자세한 근거는 ADR-036을 따른다.
- 완료 조건:
  - 각 샘플은 언어, 엔진 규칙 식별자, KISA 코드 또는 `UNMAPPED`, 취약·정상 구분, 기대 Finding 수, 기대 심각도를 기록한다.
  - 기대 Finding 수는 Semgrep 원시 매치 수가 아니라 정규화와 중복 제거 뒤 DB에 저장된 최종 Finding 수다.
  - 정규화 오류가 하나라도 나면 수를 비교하지 않고 분석이 `ENGINE_OUTPUT_INVALID`로 실패하는지 검증한다.
  - 정상 코드 검증은 전체 Finding 수가 0인지가 아니라, 해당 샘플이 검증하는 엔진 규칙이 탐지되지 않는지 확인한다.
  - Java에서 KISA 매핑 샘플을 하나도 만들 수 없으면 최소 조건을 낮추지 않고 ADR-023 절차에 따라 필요한 자체 규칙을 독자 작성해 별도 코드 리뷰 PR로 검토한다.
  - 고정 CLI, 규칙 revision, 매핑 데이터, fixture는 함께 버전 관리한다.
- 결정 필요: E4 구현 후 실제 Semgrep `check_id`, 규칙별 언어 지원, 매핑 가능 수를 확인해 fixture와 기대 결과를 확정한다.
- 테스트: 언어별 취약·정상 분석 통합 테스트, KISA 매핑과 미매핑 보존, 최종 Finding 수, 위치·심각도·신뢰도·원본 결과를 검증한다.

## 이후 작업

- E5-07 진단 결과 조회 API
- E5-08 결과 상세 화면
