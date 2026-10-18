# E7 금요일 SAST 평가와 규칙 확장 계획

## 목적과 원칙

목요일 보고는 현재 구현 범위와 판단 근거를 15분 이내로 설명한다. 금요일 평가는 실제 테스트 코드에 SecScan과 Sparrow SAST를 각각 실행해, SecScan의 탐지·KISA 연결 결과를 증거로 남기는 검증 단계다. Sparrow와의 차이는 도구의 우열이나 전체 커버리지를 단정하는 근거로 사용하지 않고, 같은 입력에서 관찰한 결과로만 기록한다.

테스트 코드와 업로드 ZIP은 저장소에 커밋하지 않는다. 저장소에는 실행한 커밋, 테스트 케이스 식별자, 기대값의 근거, 결과 집계, 로그 또는 화면 증거만 남긴다.

## 현재 기준선

- 분석 엔진은 고정 버전 Semgrep OSS 1.95.0과 SecScan 자체 규칙만 사용한다. 공식 또는 제3자 규칙은 가져오지 않는다. ADR-023을 따른다.
- 현재 실제 fixture와 KISA 매핑까지 검증한 규칙은 `secscan.java.runtime-exec → KISA-005`, `secscan.javascript.eval → KISA-002`, `secscan.python.pickle-loads → KISA-043`이다. 세 항목만 `부분 지원`이다.
- 규칙의 심각도는 매핑된 KISA 카탈로그 기본 심각도를 사용하고, 탐지 정확도에 대한 신뢰도는 검증 근거가 충분하지 않아 `UNKNOWN`으로 유지한다. ADR-032를 따른다.
- 현재 기준선의 실제 Semgrep fixture는 GitHub Actions Ubuntu 전체 `pytest -q`에서 통과한 상태여야 한다. macOS의 `RLIMIT_AS` 환경 차이는 로컬 규칙 검증의 단독 근거로 사용하지 않는다.

## E7 전체 작업 계획

E7은 새 규칙만 늘리는 에픽이 아니다. 이미 구현된 인증·권한·업로드·분석·카탈로그 기능의 허용과 거부 시나리오를 다시 실행하고, 언어별 탐지 fixture·외부 구성요소·화면·요구사항 증거를 하나의 완료 근거로 연결하는 단계다. 기존 테스트가 있는 작업도 다시 실행 결과를 남겨야 E7 증거가 된다.

| 순서 | E7 작업 | 이번에 할 일 | 완료 조건 |
|---|---|---|---|
| 1 | E7-01 인증과 역할 권한 | ADMIN/USER 로그인, 비활성 사용자, 역할별 응답 경계를 기존 테스트로 재확인 | 허용·거부 양쪽 결과와 실행 명령 기록 |
| 2 | E7-02 프로젝트 접근권한과 IDOR | 프로젝트 접근 부여·해제, 타 프로젝트 분석·Finding·소스 자원의 404를 재확인 | 비인가 404, 권한 부여 후 허용, 해제 후 재차 404 증거 |
| 3 | E7-03 파일 업로드와 작업영역 보안 | ZIP Slip, 절대·중복 경로, 심볼릭 링크, 암호화 ZIP, 크기·압축 비율 제한을 재확인 | 위험 ZIP 거부와 정상 ZIP 허용 증거 |
| 4 | E7-04 분석 상태와 오류 처리 | `PENDING → RUNNING → COMPLETED/FAILED`, timeout·자원 제한·재시작 복구를 재확인 | 상태 전이와 안전한 오류 노출 증거 |
| 5 | E7-05 KISA 카탈로그 49개 | 49개 시드의 개수·식별자·구현 상태와 ADMIN/USER 경계를 재확인 | 49개 멱등 시드와 역할별 조회·수정 경계 증거 |
| 6 | E7-06 언어별 취약·정상 fixture | 기존 3쌍과 ADR-039 신규 3쌍을 실제 Semgrep·KISA 매핑으로 검증 | 취약 fixture의 예상 Finding 1건, 정상 fixture의 대상 규칙 0건, Ubuntu CI 통과 |
| 7 | E7-07 외부 구성요소·라이선스 | Semgrep 버전·자체 규칙 출처·`pip-audit`·`npm audit` 결과를 확인 | 발견 항목과 조치 또는 잔여 위험 기록 |
| 8 | E7-08 프론트 핵심 흐름·접근성 | 로그인→프로젝트→분석 이력→결과 상세→카탈로그 흐름과 권한별 화면을 재확인 | typecheck·lint·test·build 및 핵심 화면 수동 증거 |
| 9 | E7-09 요구사항별 실행 증거 | 위 실행 결과와 CI 링크를 `docs/requirements-matrix.md`에 연결 | TST-001~008의 근거와 남은 제한 사항이 최신 상태 |

### 실행 순서

1. **기준선 확인**: E7-01~05의 기존 백엔드 테스트를 먼저 실행해, 이미 구현한 보호 기능이 규칙 확장 작업으로 회귀하지 않았는지 확인한다.
2. **1차 탐지 범위 확장**: E7-06에서 ADR-039의 SQL 삽입, DOM XSS, 경로 조작을 차례로 구현한다. 각 규칙은 fixture·매핑·provenance·CI까지 끝난 뒤 다음 규칙으로 넘어간다.
3. **2차 탐지 범위 확장**: 세 규칙이 Ubuntu CI까지 통과하면 ADR-040을 작성·검토하고 Python `os.system`, `eval`, `exec`을 각각 독립 규칙으로 구현한다.
4. **3차 탐지 범위 확장**: 2차 규칙까지 검증되면 KISA-021의 Python `hashlib.md5`·`hashlib.sha1` 직접 호출 규칙을 검토한다. checksum 용도의 오탐 가능성을 provenance와 fixture에 명시한다.
5. **공급망과 화면 검증**: E7-07과 E7-08을 실행해 의존성·라이선스와 실제 사용자 흐름의 빈틈을 확인한다.
6. **전체 회귀와 문서화**: E7-09에서 backend·frontend·CI 결과를 모으고 요구사항 검증표를 사실에 맞게 갱신한다.
7. **금요일 실측 평가**: 고정된 main 커밋으로 같은 테스트 코드를 Sparrow와 SecScan에 실행하고 아래 평가 절차에 따라 결과를 기록한다.

E7-06이 지연되면 새 규칙 개수를 약속하지 않는다. 대신 E7-01~05, E7-07~09를 완료하고, 실제로 검증된 규칙만 `부분 지원`으로 보고한다.

## 1차 확정 구현 범위

ADR-039에서 이미 결정한 다음 세 규칙만 우선 구현한다. 이 표의 항목은 구현 계획이며, fixture와 CI 증거가 생기기 전에는 카탈로그 상태를 바꾸지 않는다.

| 우선순위 | 규칙 ID | KISA 항목 | 언어 | 선언한 탐지 범위 |
|---|---|---|---|---|
| 1 | `secscan.java.jdbc-statement-sql` | KISA-001 SQL 삽입 | Java | 메서드 `String` 매개변수 → `executeQuery(String)` 또는 `executeUpdate(String)` |
| 2 | `secscan.javascript.dom-innerhtml` | KISA-004 크로스사이트 스크립트 | JavaScript | 함수 매개변수 → `$ELEMENT.innerHTML = $DATA` 직접 대입 |
| 3 | `secscan.python.open-user-path` | KISA-003 경로 조작 및 자원 삽입 | Python | 함수 매개변수 → 내장 `open($PATH, ...)` |

각 규칙은 다음 파일을 하나의 보안 구현 PR에서 함께 갱신한다.

- `backend/semgrep-rules/secscan-security.yml`: 자체 규칙 YAML
- `backend/semgrep-rules/RULES_PROVENANCE.md`: 공개 근거, 정확한 sink 범위와 제외 범위
- `backend/app/services/kisa_catalog_seed.py`: `KISA_RULE_MAPPING_SEED`와 검증 완료 뒤의 구현 상태
- `backend/tests/fixtures/vulnerable/`, `backend/tests/fixtures/safe/`: 취약·정상 fixture
- `backend/tests/test_e5_result_normalization.py`: 실제 Semgrep 실행, 예상 규칙 ID, KISA 코드, 정상 fixture 미탐지
- `docs/epic/e5-result-normalization.md`, `docs/requirements-matrix.md`: 구현과 검증이 끝난 뒤에만 상태·증거 갱신

### 규칙별 정상 fixture와 제외 범위

- SQL 삽입 정상 fixture는 바인딩 파라미터를 사용하는 `PreparedStatement`여야 한다. `execute(String)`, `executeUpdate(String, int)`, ORM, JPA는 이번 규칙 범위 밖이다.
- DOM XSS 정상 fixture는 동일한 함수 매개변수를 `textContent`에 대입하거나, `innerHTML`에 고정 문자열을 넣어야 한다. `innerHTML +=`, `insertAdjacentHTML`, JSX·템플릿·SSR·프레임워크 sanitizer는 범위 밖이다.
- 경로 조작 정상 fixture는 고정 서버 관리 경로를 사용해야 한다. `Path.open`, `os.open`, `shutil`, 압축 해제 경로와 로컬에서 재정의한 `open`은 범위 밖이다.

### 규칙 전환 게이트

각 규칙은 아래 네 가지가 모두 충족될 때만 매핑 시드와 카탈로그의 `부분 지원` 상태를 추가한다.

1. 고정 YAML을 `--no-rewrite-rule-ids`와 함께 Semgrep OSS 1.95.0으로 직접 실행했을 때 취약 fixture에서 예상한 접두어 없는 `check_id`가 정확히 한 건 나온다.
2. 정상 fixture에서 검증 대상 `check_id`가 0건 나온다. 이는 모든 안전한 변형의 무결성을 증명하는 것이 아니라 선언한 source-to-sink 형태의 최소 회귀 검증이다.
3. `test_real_semgrep_vulnerable_fixtures_normalize_to_mapped_findings`, `test_real_semgrep_safe_fixtures_do_not_trigger_the_tested_rule`에 같은 기준으로 테스트를 추가한다.
4. GitHub Actions Ubuntu의 필터 없는 `pytest -q`와 관련 CI job이 통과한다.

세 규칙이 모두 이 게이트를 통과하면 실제 `부분 지원` KISA 항목은 초기 3개에서 6개가 된다. 이는 고정된 목표 수가 아니라 해당 revision에서 검증된 범위일 뿐이며, 각 항목의 모든 언어·API 변형을 지원한다는 뜻은 아니다.

## 완료 뒤 진행할 확장 백로그

아래 작업은 앞 단계의 규칙·fixture·CI가 모두 끝나면 바로 다음 순서로 진행한다. 기존 KISA 항목에 새 언어 규칙을 더하는 결정은 ADR-039에 없으므로, 2차 확장 구현 전에 ADR-040을 작성하고 Claude 리뷰를 받아야 한다.

| 순서 | 후보 | 예정 규칙 ID | 이유 | 선행 조건 |
|---|---|---|---|
| 4 | KISA-005 Python 운영체제 명령어 삽입 | `secscan.python.os-system` | 기존 KISA-005에 Python `os.system()` sink 추가 | ADR-040, 취약·정상 fixture, CI |
| 5 | KISA-002 Python 코드 삽입 | `secscan.python.eval` | Python `eval` sink을 독립 규칙으로 추가 | ADR-040, 규칙별 fixture, CI |
| 6 | KISA-002 Python 코드 삽입 | `secscan.python.exec` | Python `exec` sink을 독립 규칙으로 추가 | ADR-040, 규칙별 fixture, CI |
| 7 | KISA-021 취약한 암호화 알고리즘 사용 | 미정 | Python `hashlib.md5`·`hashlib.sha1` 직접 호출의 제한된 패턴 | 별도 fixture·오탐 범위 기록·CI |

KISA-043 Java 역직렬화는 타입·스트림 형태의 모호성이 크고, KISA-023 하드코드된 중요정보는 placeholder와 test fixture에서 오탐 위험이 커서 이번 주에는 시도하지 않는다. 부재 기반 판정이나 프레임워크 해석이 필요한 규칙도 빠른 추가보다 오탐 위험이 크므로 같은 원칙으로 제외한다.

## 금요일 SAST 평가 절차

### 1. 사전 준비

1. 평가에 사용할 SecScan 커밋 SHA, Docker 이미지 또는 실행 환경, Semgrep 버전, 규칙 revision을 기록한다.
2. 테스트 코드의 언어, 파일 수, 입력 식별자와 SHA-256을 기록한다. 원본 코드는 저장소에 넣지 않는다.
3. 각 테스트 케이스에 기대 취약 여부와 근거를 확보한다. 기대값이 없는 항목은 정탐·오탐·미탐으로 단정하지 않고 `판정 보류`로 둔다.

### 2. 실행과 기록

1. 같은 테스트 코드를 Sparrow SAST와 SecScan에 각각 실행한다.
2. SecScan은 업로드 시각, 분석 시작·완료 시각, 상태, 실행 시간, 엔진 규칙 ID, KISA 코드, 파일·줄 위치를 기록한다.
3. 각 결과는 다음 표의 한 행으로 남긴다.

| 케이스 | 언어 | 기대 | SecScan 탐지 | 엔진 규칙 ID | KISA 연결 | 판정 | 메모 |
|---|---|---|---|---|---|---|---|
| 예: CASE-01 | Java | 취약 | 탐지 | `secscan.java.jdbc-statement-sql` | KISA-001 | TP | 선언한 JDBC sink 범위 안 |

### 3. 판정 규칙

| 기대 상태 | SecScan 결과 | 판정 |
|---|---|---|
| 취약 | 탐지 | 정탐(TP) |
| 정상 | 탐지 | 오탐(FP) |
| 취약 | 미탐 | 미탐(FN) |
| 정상 | 미탐 | 정상 미탐(TN) |
| 규칙의 선언 범위 밖 | 미탐 | 범위 외 |
| 탐지했지만 예상 KISA 코드와 다름 | 탐지 결과와 별도로 `매핑 오류` 기록 |
| 기대 상태의 근거 없음 | 판정 보류 |

`범위 외`는 미탐을 숨기기 위한 표기가 아니다. ADR과 provenance에 명시한 source·sink 범위를 벗어나 평가 대상 규칙이 원래 탐지하겠다고 선언하지 않은 경우에만 사용한다.

### 4. 평가 후 반영

- 각 규칙별 TP/FP/FN/TN 수, 매핑 오류 수, 범위 외 수와 대표 사례를 기록한다.
- 오탐·미탐은 규칙 ID, source·sink 형태, 파일·줄, 재현 방법과 함께 이슈 또는 트러블슈팅 문서에 남긴다.
- 검증에 실패한 규칙은 `부분 지원`으로 전환하지 않거나, 이미 전환된 경우 근거와 함께 상태를 재검토한다.
- 검증이 완료된 규칙만 `RULES_PROVENANCE.md`, E5 문서, 요구사항 검증표에 실행 증거를 추가한다.

## 작업 순서와 중단 기준

1. ADR-039 SQL 삽입 구현과 fixture 검증
2. ADR-039 DOM XSS 구현과 fixture 검증
3. ADR-039 경로 조작 구현과 fixture 검증
4. 세 규칙을 포함한 Ubuntu CI 통과 확인
5. ADR-040 작성·검토 뒤 Python `os.system`, `eval`, `exec`을 차례로 구현·검증
6. 2차 확장이 CI까지 통과하면 KISA-021 약한 해시 규칙 검토·구현
7. 금요일 평가용 실행 기록표 준비

다음 중 하나가 발생하면 다음 규칙 추가를 멈추고 현재 증거를 정리한다.

- 신규 규칙이 취약·정상 fixture 기대값을 만족하지 않는다.
- Ubuntu CI에서 실제 Semgrep fixture 또는 전체 회귀가 실패한다.
- 새 규칙에 필요한 API·프레임워크·sanitizer 해석이 ADR에 선언한 제한 범위를 넘어선다.
- 평가 코드의 기대값이 없어 TP/FP/FN을 신뢰성 있게 판정할 수 없다.

## Sparrow 비교 평가 기록

금요일에는 동일한 취약·정상 fixture를 SecScan과 Sparrow에 각각 입력한다. 두 제품의
탐지 결과를 단순히 우열로 비교하지 않고, 탐지 여부·위치·심각도·KISA 연결 여부·근거
제공 여부의 차이로 기록한다.

| 비교 항목 | SecScan | Sparrow | 차이·판정 |
|---|---|---|---|
| 취약 코드 탐지 여부 | 평가 후 기록 | 평가 후 기록 | TP/미탐 여부 |
| 정상 코드 미탐지 여부 | 평가 후 기록 | 평가 후 기록 | TN/오탐 여부 |
| 파일 위치·코드 위치 | 평가 후 기록 | 평가 후 기록 | 위치 일치 여부 |
| 심각도 | KISA 카탈로그 기준 | 평가 후 기록 | 분류 차이 |
| KISA 기준 연결 | 자체 매핑표 기준 | 평가 후 기록 | 매핑 가능 여부 |
| 탐지 근거 | 결과 상세에서 제공 | 평가 후 기록 | 근거 설명 차이 |
| 조치 권고 | 결과 상세에서 제공 | 평가 후 기록 | 권고 내용 차이 |

- SecScan의 현재 TP/TN 수치는 선언한 fixture에 한정하며, Sparrow 결과와 합산하지 않는다.
- 표의 SecScan 기입값은 금요일 평가 결과가 아니라 현재 구현된 기능을 설명한 것이다.
- 외부 표본에서 기대값이 불명확한 결과는 `판정 보류`로 기록한다.
- KISA 49개 전체 탐지 여부나 두 제품의 종합 우열을 이 비교만으로 주장하지 않는다.

## 관련 문서

- `docs/adr/023-vendored-semgrep-security-rules.md`
- `docs/adr/030-engine-rule-to-kisa-mapping-table.md`
- `docs/adr/032-finding-severity-confidence-normalization.md`
- `docs/adr/036-language-fixture-priority.md`
- `docs/adr/039-self-authored-rule-coverage-expansion.md`
- `docs/adr/040-python-rule-extensions-for-existing-kisa-codes.md`
- `docs/epic/e5-result-normalization.md`
- `docs/epic/epic-sast-mvp.md`
- `docs/requirements-matrix.md`

## E7 최종 검증 실행 기록 (2026-09-01)

### 실행 기준

- 대상 revision: `269738bfa2e5fbd64db3de78d1c660c6bedd2ee2`
  (`feat(e5): Python 자체 규칙 확장 검증 보완`)
- 실행 환경: 읽기 전용 backend 소스를 마운트한 Linux Docker(Python 3.12),
  PostgreSQL 16 전용 `_test` 데이터베이스, Semgrep OSS 1.95.0.
- 검증 명령: Linux 컨테이너에서 `pytest -q -p no:cacheprovider`를 실행했다.
  GitHub Actions Ubuntu runner 자체의 실행 결과는 아니므로 이 기록으로 GitHub CI 통과를
  대체하지 않는다.

### 부분 지원 KISA 규칙 fixture 판정

`test_real_semgrep_vulnerable_fixtures_normalize_to_mapped_findings`는 각 취약 fixture에서
예상 `check_id` 정확히 1건, 정규화된 Finding 1건, 기대 KISA 코드, `HIGH/UNKNOWN`을
검증한다. `test_real_semgrep_safe_fixtures_do_not_trigger_the_tested_rule`는 해당 대상
규칙이 정상 fixture에서 나오지 않음을 검증한다.

| KISA 코드 | 검증한 엔진 규칙 | TP | TN | FP | FN | 판정 보류 |
|---|---|---:|---:|---:|---:|---:|
| KISA-001 | `secscan.java.jdbc-statement-sql` | 2 | 1 | 0 | 0 | 0 |
| KISA-002 | `secscan.javascript.eval`, `secscan.python.eval`, `secscan.python.exec` | 3 | 3 | 0 | 0 | 0 |
| KISA-003 | `secscan.python.open-user-path` | 1 | 1 | 0 | 0 | 0 |
| KISA-004 | `secscan.javascript.dom-innerhtml` | 14 | 1 | 0 | 0 | 0 |
| KISA-005 | `secscan.java.runtime-exec`, `secscan.python.os-system` | 2 | 5 | 0 | 0 | 0 |
| KISA-043 | `secscan.python.pickle-loads` | 1 | 1 | 0 | 0 | 0 |
| 합계 | 현재 `부분 지원` 6개 KISA 코드 | **23** | **12** | **0** | **0** | **0** |

- KISA 연결 오류는 0건이다. 같은 테스트의 시드 검증은 위 6개 코드만 `부분 지원`이고
  나머지 카탈로그 항목은 `미지원`임을 확인한다.
- TP/TN/FP/FN은 선언한 source-to-sink 형태와 이 35개 제어 fixture에 한정한 수치다.
  범위 밖 API·프레임워크·sanitizer 변형과 실제 서비스 코드 표본은 이번 실행에 기대값이
  없으므로 정확도 수치에 포함하지 않았으며, 전수 KISA-49 탐지·커버리지를 뜻하지 않는다.
- 기대값 근거가 없는 fixture는 0건이지만, 23개 TP Finding의 탐지 신뢰도는 ADR-032에 따라
  모두 `UNKNOWN`이다. 이 값은 TP 판정과 별개이며, 독립 표본을 통한 정밀도·재현율 평가는
  여전히 미확인이다.

### 보호 기능과 전체 회귀

| 검증 영역 | 실행된 백엔드 테스트 | 결과 |
|---|---:|---|
| 인증·역할 권한 | 23 (`test_auth_api.py` 18, `test_auth_authorization.py` 5) | 통과 |
| 프로젝트 접근·IDOR | 10 (`test_project_access_api.py` 5, `test_project_resource_access.py` 5) | 통과 |
| ZIP 보안·작업영역 | 46 (`test_source_archive.py` 18, `test_source_upload_api.py` 21, `test_source_workspace.py` 7) | 통과 |
| 분석 상태·복구 | 20 (`test_analysis_api.py` 3, `test_analysis_schema.py` 13, `test_analysis_execution.py` 3, `test_analysis_startup_recovery.py` 1) | 통과 |
| 결과 접근·역할별 응답 | 14 (`test_api_contract.py` 9, `test_e6_findings_api.py` 5) | 통과 |
| KISA 매핑·fixture | 41 (`test_e5_result_normalization.py`) | 통과 |

- 전체 backend: **244 passed**, 경고 5건, 실패 0건 (139.56초).
- frontend: ESLint 통과, TypeScript typecheck 통과, Vitest **44 passed** (4 files),
  production build 통과. React Router v7 future-flag 경고만 관찰됐고 테스트 실패는 없었다.
- macOS 네이티브 실행은 `RLIMIT_AS`로 실제 Semgrep fixture 35개가
  `ANALYSIS_RESOURCE_LIMIT`로 실패했다. 이는 기존
  `docs/troubleshooting/2026-09-01-e5-local-semgrep-sandbox-validation.md`의 환경 제한과
  일치하며, 같은 revision의 Linux Docker 전체 backend 실행에서는 재현되지 않았다.

### 남은 미확인 범위

- Sparrow와 같은 입력을 비교하는 금요일 실측 평가는 이 SecScan 검증 실행에 포함하지 않았다.
- GitHub Actions Ubuntu runner의 실제 job 결과와 외부·실서비스 표본에 대한 TP/FP/FN은
  아직 이 문서의 실행 증거가 아니다.
- 현재 결론은 6개 부분 지원 KISA 코드의 선언 범위 검증이며, KISA 49개 전체의 구현 또는
  탐지 커버리지를 주장하지 않는다.
