# ADR-040: 기존 KISA 항목의 Python 자체 규칙 확장

**Context**: ADR-039 구현·Ubuntu CI 검증 뒤 SecScan은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043 여섯 항목을 제한된 자체 Semgrep 규칙 범위로 `부분 지원`한다. 이 중 KISA-005 운영체제 명령어 삽입은 Java `Runtime.getRuntime().exec(...)` 규칙만, KISA-002 코드 삽입은 JavaScript `eval(...)` 규칙만 연결되어 있다. `KISA_RULE_MAPPING`은 하나의 KISA 항목에 여러 엔진 규칙을 연결하도록 설계됐으므로(ADR-030), 검증 가능한 Python 위험 API를 별도 규칙으로 추가할 수 있다.

**Decision**: 고정 Semgrep OSS와 SecScan 자체 작성 규칙만 유지하면서, 아래 Python `mode: taint` 규칙을 각각 독립된 `engine_rule_id`로 추가한다. 함수 매개변수가 지정한 위험 API에 직접 도달하는 경우만 다루며, `eval`과 `exec`은 서로 다른 sink와 fixture를 가지므로 하나의 규칙으로 합치지 않는다.

| 규칙 ID | KISA 항목 | source → sink 범위 | 공개 근거 |
|---|---|---|---|
| `secscan.python.os-system` | KISA-005 운영체제 명령어 삽입 | 함수 매개변수 → `os.system($COMMAND)` | CWE-78, OWASP A03:2021 |
| `secscan.python.eval` | KISA-002 코드 삽입 | 함수 매개변수 → 내장 `eval($CODE)` | CWE-95, OWASP A03:2021 |
| `secscan.python.exec` | KISA-002 코드 삽입 | 함수 매개변수 → 내장 `exec($CODE)` | CWE-95, OWASP A03:2021 |

- `os.system` 규칙은 `subprocess.run`, `subprocess.Popen`, `os.popen`, 셸 문자열 조합의 모든 변형, 로컬에서 재정의한 `os` 이름을 포함하지 않는다.
- `eval`·`exec` 규칙은 bare builtin 호출만 포함한다. 로컬에서 `eval`·`exec` 이름을 재정의한 코드, sanitizer·허용 목록, 간접 호출과 framework별 입력 추적은 구분하지 않는다.
- 각 규칙은 취약 fixture에서 예상한 접두어 없는 `check_id` 정확히 한 건, 같은 sink의 고정값 정상 fixture에서 대상 규칙 0건을 확인한다. 이는 모든 안전한 변형을 증명하는 것이 아니라, 선언한 source-to-sink 형태의 최소 회귀 검증이다.
- 매핑 시드는 `secscan.python.os-system → KISA-005`, `secscan.python.eval → KISA-002`, `secscan.python.exec → KISA-002`로 추가한다. KISA-005와 KISA-002는 이미 `부분 지원`이므로 카탈로그 구현 상태를 `지원`으로 올리거나 부분 지원 항목 수를 늘리지 않는다.
- 규칙 YAML, `RULES_PROVENANCE.md`, 매핑 시드, fixture, E5 정규화 테스트, 요구사항 증거는 하나의 보안 구현 PR에서 함께 변경한다. 직접 Semgrep 실행과 GitHub Actions Ubuntu의 필터 없는 `pytest -q`가 모두 통과한 뒤에만 병합한다.

**Alternatives**: JavaScript·Java의 기존 규칙만 유지, `eval`과 `exec`을 하나의 다중 sink 규칙으로 결합, `subprocess` 계열까지 한 번에 추가, KISA-021 약한 해시나 KISA-023 하드코드된 중요정보를 먼저 추가, 공식 또는 제3자 Semgrep 규칙 사용

**Consequences**: 기존 KISA 코드에 Python 탐지 경로가 추가돼 언어별 검증 범위가 넓어진다. 반면 새 규칙도 정확한 API·문법 형태만 다루며, broad function parameter source와 sanitizer 미모델링으로 오탐·미탐 가능성이 있다. 신뢰도는 실제 검증 근거가 충분해질 때까지 `UNKNOWN`으로 유지한다. KISA-043 Java 역직렬화, KISA-021, KISA-023은 이 결정의 범위에 포함하지 않는다.

**References**: ADR-023, ADR-030, ADR-032, ADR-036, ADR-039, SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
