# E5 결과 정규화와 KISA 매핑 작업 상세

E5는 E4가 실행한 Semgrep JSON 결과를 엔진 독립적인 진단 결과로 정규화하고, 가능한 결과를 KISA 카탈로그와 연결해 Finding으로 저장한다. E5의 백엔드 정규화·매핑·저장 범위와 언어별 fixture 검증은 2026-08-29에 완료했다. 결과 목록·상세 UI는 E6 범위다.

## E5-01, E5-02 외부 결과 파서와 공통 진단 결과 변환기

- 상태: 완료 (2026-08-29)
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
- 확정 입력: E5 구현은 고정 YAML 파일을 직접 `--config`로 지정해 YAML `id`와 같은 접두어 없는 Semgrep `check_id`를 `engine_rule_id`로 사용한다. 표시명, 심각도·신뢰도와 탐지 근거의 실제 필드 규칙은 E5-04·E5-05를 따른다.
- 테스트·증거: `backend/tests/test_e5_result_normalization.py`가 Semgrep 파싱, 지문 중복 제거, 매핑·미매핑 정규화, 상대 경로 원본 결과 보존을 검증했다. 2026-08-29 전용 PostgreSQL 전체 백엔드 pytest 208개와 Ruff를 통과했다.

## E5-03 KISA 항목 매핑 규칙

- 상태: 완료 (2026-08-29)
- 요구사항 매핑: SFR-010, SFR-012, SFR-013, SFR-014, QLT-002, QLT-003, SEC-010
- 결정과 근거: `KISA_RULE_MAPPING`이 엔진 규칙과 KISA 항목을 연결한다. 한 KISA 항목에는 여러 언어·패턴 규칙을 연결할 수 있고, `UNIQUE(engine, engine_rule_id)`로 하나의 규칙이 여러 KISA 항목에 중복 연결되는 것을 막는다. 기존 `KISA_CATALOG.semgrep_rule_id`는 E5 migration에서 제거한다. 매핑은 API나 관리자 UI가 아닌 코드 리뷰 PR의 시드 또는 버전 관리 데이터로 관리한다. 자세한 근거는 ADR-030을 따른다.
- 완료 조건:
  - `KISA_RULE_MAPPING`에 `engine`, `engine_rule_id`, `kisa_code`와 복합 UNIQUE·외래키 제약이 있다.
  - KISA 항목 하나에 여러 Semgrep 규칙을 연결할 수 있다.
  - 동일한 `(engine, engine_rule_id)`는 두 KISA 항목에 연결되지 않는다.
  - `KISA_CATALOG.semgrep_rule_id`와 현재 이를 노출하는 `CatalogItemOut` 필드는 E5 migration에서 제거한다. 생성·수정 스키마에는 매핑 필드를 추가하지 않는다.
  - `/api/rule-mappings` 같은 매핑 관리 API는 만들지 않는다.
  - 고정 YAML을 직접 지정한 Semgrep 출력의 `check_id`만 매핑 시드에 사용한다.
  - 초기 매핑 시드는 `secscan.java.runtime-exec → KISA-005`, `secscan.javascript.eval → KISA-002`, `secscan.python.pickle-loads → KISA-043`이다.
  - 세 대응 KISA 항목의 구현 상태는 현재 source-to-sink 패턴 범위만 지원하므로 `부분 지원`으로 갱신한다.
- 확정 입력: E5에서 자체 규칙을 taint 방식으로 보완한 뒤, 고정 Semgrep CLI의 실제 `check_id`가 위 시드 값과 일치하는지 fixture 실행으로 다시 확인한다.
- 테스트·증거: `backend/tests/test_e5_result_normalization.py`가 매핑 제약, 시드 상태, 매핑·미매핑 결과 저장을 검증했다. 실제 고정 YAML 실행의 `check_id` 세 값도 시드와 일치함을 확인했다.

## E5-04 미매핑 결과 보존과 역할별 노출

- 상태: 완료 (2026-08-29)
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
- 확정 입력: 초기 자체 규칙의 실제 Semgrep 출력은 `extra.severity: ERROR`을 제공하고 신뢰도 메타데이터는 제공하지 않는다. 초기 세 매핑 결과는 KISA 카탈로그의 `HIGH`를 심각도로 복사하고, 신뢰도는 `UNKNOWN`으로 저장한다. 미매핑 결과와 후속 규칙은 ADR-032의 공통 정규화 규칙을 따른다.
- 테스트·증거: `backend/tests/test_e5_result_normalization.py`, `backend/tests/test_finding_schema.py`가 미매핑 보존, 역할별 `raw_result` 경계, 심각도·신뢰도·매핑 제약을 검증했다.

## E5-05 탐지 근거, 코드 조각과 조치 권고

- 상태: 완료 (2026-08-29)
- 요구사항 매핑: SFR-009, SFR-014, DAR-006, DAR-008, SEC-003, SEC-008, QLT-004
- 결정과 근거: `message`는 엔진이 제공한 짧은 진단 설명을 저장한다. `evidence`는 고정 Semgrep 출력에서 얻는 안전한 탐지 근거를 최대 2 KiB로 저장하며, 근거가 없으면 엔진 규칙 식별자와 상대 파일 범위를 이용한 짧은 대체 문구를 저장한다. `code_snippet`은 엔진 원본 출력에 의존하지 않고 분석 시점 소스 스냅샷에서 추출한다. 시작 `line`과 끝 `end_line` 전후 2줄을 포함하되 원본 코드 줄은 최대 20줄, 전체 텍스트는 최대 8 KiB로 제한한다. 범위가 길면 탐지 범위의 앞뒤를 남기고 생략 표식을 넣는다. 코드 조각은 전체 소스 뷰어가 아니며, 권한 있는 USER와 ADMIN의 Finding 응답에 포함한다. 자세한 근거는 ADR-033을 따른다.
- 완료 조건:
  - `line`은 시작 줄이며 `end_line`은 끝 줄이다. `end_line`은 NULL을 허용하지만 두 값이 있으면 `end_line >= line`만 저장된다.
  - Semgrep 결과의 시작·끝 줄을 각각 저장하고, 단일 줄 결과는 같은 값을 저장한다.
  - 코드 조각 추출 전 `snapshot_root / file_path`의 해석 경로가 분석 스냅샷 루트 안에 있는지 재검증한다.
  - 코드 조각은 상대 경로와 제한된 줄 범위만 사용하며, 서버 내부 경로, 전체 파일, 원본 ZIP 파일명은 포함하지 않는다.
  - 코드 조각을 만들 수 없어도 Finding 저장과 분석 완료는 실패하지 않으며, 이 경우 위치, 메시지, 탐지 근거와 조치 권고는 저장한다.
  - 매핑 결과의 `recommendation`은 정규화 시점 KISA 카탈로그 값을 복사하고, 미매핑 결과는 NULL로 둔다.
- 확정 입력: `message`는 `extra.message`, `evidence`는 `extra.metadata.secscan_basis`를 우선 사용한다. `secscan_basis`가 없으면 기존의 규칙 식별자·상대 파일 범위 대체 문구를 사용한다. `extra.lines`와 `metavars`는 사용자용 근거로 사용하지 않는다.
- 테스트·증거: `backend/tests/test_e5_result_normalization.py`가 스냅샷 내부 경로 재검증과 코드 조각 추출 실패 뒤 Finding 보존을 검증했다. `backend/tests/test_migrations.py`가 끝 줄·심각도·신뢰도 제약을 실제 PostgreSQL에서 확인했다.

## E5-06 원본 결과와 분석 시점 보존

- 상태: 완료 (2026-08-29)
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
- 테스트·증거: `backend/tests/test_e5_result_normalization.py`, `backend/tests/test_analysis_execution.py`가 개별 원본 결과, 안전한 Analysis 실행 메타데이터, `ENGINE_OUTPUT_INVALID` 전체 롤백을 검증했다.

## E5-09 언어별 취약 코드와 정상 코드 테스트

- 상태: 완료 (2026-08-29)
- 요구사항 매핑: SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
- 결정과 근거: Java, JavaScript, Python은 모두 MVP 지원 언어로 유지한다. E4가 고정한 Semgrep CLI와 SecScan 자체 작성 고정 규칙을 실제 실행해 언어별 지원 규칙을 확인한 뒤, 각 언어에서 KISA 매핑 취약 코드와 같은 규칙이 탐지되지 않아야 하는 정상 코드를 최소 하나씩 만든다. 실제 샘플은 KISA 매핑의 명확성, 다언어 지원 여부, 취약·정상 차이의 설명 가능성, 재현 안정성 순으로 늘린다. 고정 탐지 항목 수는 정하지 않고 검증 가능한 항목을 최대한 추가한다. TypeScript는 확장 구조만 유지하고 후순위로 둔다. 자세한 근거는 ADR-036을 따른다.
- 완료 조건:
  - Java는 외부 입력→`Runtime.exec`(취약)과 고정 명령→`Runtime.exec`(정상), JavaScript는 외부 입력→`eval`(취약)과 고정 문자열→`eval`(정상), Python은 외부 입력→`pickle.loads`(취약)과 신뢰된 고정 바이트→`pickle.loads`(정상) fixture를 각각 둔다.
  - 각 취약 샘플은 한 건의 KISA 매핑 Finding(`KISA-005`, `KISA-002`, `KISA-043` 순), 심각도 `HIGH`, 신뢰도 `UNKNOWN`을 기대한다. 각 정상 샘플은 검증 대상 규칙의 미탐지를 기대한다.
  - 각 샘플은 언어, 엔진 규칙 식별자, KISA 코드 또는 `UNMAPPED`, 취약·정상 구분, 기대 Finding 수, 기대 심각도를 기록한다.
  - 기대 Finding 수는 Semgrep 원시 매치 수가 아니라 정규화와 중복 제거 뒤 DB에 저장된 최종 Finding 수다.
  - 정규화 오류가 하나라도 나면 수를 비교하지 않고 분석이 `ENGINE_OUTPUT_INVALID`로 실패하는지 검증한다.
  - 정상 코드 검증은 전체 Finding 수가 0인지가 아니라, 해당 샘플이 검증하는 엔진 규칙이 탐지되지 않는지 확인한다.
  - Java에서 KISA 매핑 샘플을 하나도 만들 수 없으면 최소 조건을 낮추지 않고 ADR-023 절차에 따라 필요한 자체 규칙을 독자 작성해 별도 코드 리뷰 PR로 검토한다.
  - 고정 CLI, 규칙 revision, 매핑 데이터, fixture는 함께 버전 관리한다.
  - `mode: taint`의 `pattern-sources` 표현과 취약 fixture의 외부 입력 표현은 같은 변경에서 함께 검토한다.
  - 실제 서비스 규칙이 모두 KISA에 매핑되어도, 미매핑 결과 보존은 테스트 전용 합성 Semgrep JSON fixture로 검증한다.
- 테스트·증거: 2026-08-29 기준 `backend/tests/test_e5_result_normalization.py`가 Java, JavaScript, Python의 초기 실제 taint 취약 fixture(KISA-005/002/043, HIGH, UNKNOWN)와 같은 sink의 정상 fixture 미탐지를 검증했다. ADR-039·ADR-040 확장 증거는 E5-10을 따른다.

## E5-10 자체 규칙 커버리지 확장

- 상태: 구현·로컬 검증 완료, Ubuntu CI 확인 대기 (2026-09-01)
- 요구사항 매핑: SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, SEC-010
- 결정과 근거: 초기 세 자체 규칙은 실제 탐지 범위를 정직하게 보여 주지만 카탈로그 49개 가운데 `부분 지원` 항목이 세 개뿐이었다. ADR-039는 Java SQL 삽입, JavaScript DOM XSS, Python `open()` 경로 조작을 각각 한 개씩 추가했고, ADR-040은 기존 KISA-005에 Python `os.system()`을, 기존 KISA-002에 Python bare `eval()`·bare `exec()`을 각각 독립 규칙으로 추가한다. 공식 또는 제3자 규칙을 가져오지 않으며, 모든 규칙은 제한된 source-to-sink 문법만 다루므로 `지원`으로 승격하지 않는다. 자세한 범위와 제외 항목은 ADR-039·ADR-040을 따른다.
- 완료 조건:
  - `secscan.java.jdbc-statement-sql`은 Java `String` 매개변수에서 `executeQuery(String)` 또는 `executeUpdate(String)`으로 흐르는 SQL을 탐지하고 KISA-001에 매핑한다. 메서드명 기반 규칙이므로 한 인자를 받는 동명 `PreparedStatement` 호출도 범위에 포함하며, 바인딩 뒤 인자 없이 호출하는 `PreparedStatement.executeQuery()`/`executeUpdate()`, bare `execute(String)`, `executeUpdate(String, int)`, ORM/JPA는 탐지하지 않는다.
  - `secscan.javascript.dom-innerhtml`은 JavaScript 함수 매개변수에서 `$ELEMENT.innerHTML = $DATA` 패턴으로 흐르는 값을 탐지하고 KISA-004에 매핑한다. 고정 Semgrep OSS 1.95.0은 이 패턴으로 `innerHTML +=`도 같은 규칙 ID로 탐지하므로 별도 `+=` 규칙은 만들지 않는다. React·템플릿·SSR·`insertAdjacentHTML`은 탐지하지 않는다.
  - `secscan.python.open-user-path`는 Python 함수 매개변수에서 내장 `open()`으로 흐르는 경로를 탐지하고 KISA-003에 매핑한다. `Path.open`, `os.open`, `shutil`, 압축 해제와 업로드 경로 검증은 탐지하지 않는다.
  - `secscan.python.os-system`은 `import os`가 있는 Python 파일의 함수 매개변수에서 `os.system()`으로 직접 흐르는 값을 탐지하고 KISA-005에 매핑한다. `subprocess` 계열, `os.popen`, 셸 문자열 조합은 탐지하지 않으며, 이름 해석은 하지 않으므로 로컬에서 재정의한 `os` 이름은 구분하지 않는다.
  - `secscan.python.eval`과 `secscan.python.exec`은 Python 함수 매개변수에서 각각 `eval()`과 `exec()` 이름 호출로 직접 흐르는 값을 탐지하고 KISA-002에 매핑한다. sanitizer·허용 목록, 간접 호출과 framework별 입력 추적은 탐지하지 않으며, 이름 해석은 하지 않으므로 로컬에서 재정의한 `eval`·`exec` 이름도 구분하지 않는다.
  - 각 신규 규칙은 `RULES_PROVENANCE.md`에 규칙 ID, KISA/CWE/OWASP 근거, source·sink, 타입·이름 기반 매칭 한계를 기록한다.
  - 각 신규 취약 fixture는 실제 Semgrep OSS를 고정 YAML 파일과 `--no-rewrite-rule-ids`로 직접 실행해 정확히 한 건의 접두어 없는 `check_id`를 낸다. 이 값, KISA 매핑 시드와 기대 Finding ID가 일치한다.
  - 각 신규 정상 fixture는 검증 대상 규칙의 미탐지를 확인한다. Java PreparedStatement와 Python 고정 경로 fixture는 모든 안전화 기법을 인증하는 테스트가 아니라, 이번 sink 형태가 없음을 검증하는 범위로 설명한다.
  - 여섯 매핑 KISA 항목(KISA-001/002/003/004/005/043)만 `부분 지원`이고, 나머지 항목은 구현 검증 전까지 `미지원`으로 유지한다.
  - 신규 규칙·매핑·fixture의 집중 테스트와 전용 PostgreSQL 전체 백엔드 pytest, Ruff, `git diff --check`를 통과한다.
- 테스트·증거: Semgrep OSS 1.95.0을 고정 YAML과 `--no-rewrite-rule-ids`로 직접 실행해 ADR-039·ADR-040의 여섯 규칙 취약 fixture에서 각각 접두어 없는 기대 `check_id` 한 건을 확인했고, 고정값 및 `import os`가 없는 `os` 이름 형태의 안전 fixture에서는 대상 규칙을 확인하지 못했다. Java는 package-private `executeQuery(String)`과 private static `executeUpdate(String)`, JavaScript는 선언·익명·async 함수, 블록·표현식 본문 화살표 함수(단일·다중·괄호 없음), async 클래스·동기 객체 메서드, Python은 async `open()` 함수와 ADR-040의 `os.system()`·`eval()`·`exec()`을 함께 검증한다. async 객체 축약 메서드는 Semgrep OSS 1.95.0 규칙 패턴 문법 한계로 제외했다. 변경하지 않은 리소스 래퍼를 포함한 전용 PostgreSQL Docker 환경에서 `pytest -q tests/test_e5_result_normalization.py` 41개와 `ruff check .`를 통과했다. 최종 GitHub Actions Ubuntu의 필터 없는 `pytest -q` 확인은 push/PR 금지 범위 밖이므로 사람 검토·병합 전에 남아 있다.

## 구현·검증 결과

- E5-01~06, E5-09: `semgrep_parser.py`와 `finding_normalizer.py`가 Semgrep 결과를 정규화하고, KISA 매핑·스냅샷·지문 중복 제거를 하나의 DB 트랜잭션으로 저장한다.
- E5-07: 결과 조회 API 자체는 E1-07에서 구현돼 있으며, E5는 해당 응답 스키마에 `engine_rule_id`와 역할별 원본 결과 경계를 반영했다. 새 조회 엔드포인트는 만들지 않았다.
- E5-08: 결과 목록·상세 화면은 `E6-03`, `E6-04` 범위로 이관한다.
- 2026-08-29 기준선 검증: 전용 PostgreSQL에서 Alembic `upgrade head → downgrade 0007 → upgrade head`, E5 집중 pytest 20개, 전체 backend pytest 208개, `ruff check app tests`, `git diff --check`을 통과했다. ADR-039 확장의 현재 로컬 증거는 E5-10을 따른다.

## 이후 작업

- 기존 6개 KISA 항목의 직접 API 커버리지 확장 계획: `docs/epic/e5-kisa-six-code-coverage-expansion.md` 및 ADR-041. 이 계획은 구현 증거가 아니며, 각 예정 규칙은 독립 fixture와 Ubuntu CI 게이트를 통과한 뒤에만 E5-10 증거를 갱신한다.
- E6-03 진단 결과 목록과 필터 UI
- E6-04 진단 결과 상세 패널 UI
