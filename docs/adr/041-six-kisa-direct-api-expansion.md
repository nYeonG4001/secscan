# ADR-041: 기존 6개 KISA 항목의 직접 API 탐지 범위 확장

**Context**: ADR-039와 ADR-040까지 구현·검증된 자체 Semgrep 규칙은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043 여섯 항목을 제한된 문법적 source-to-sink 형태로 `부분 지원`한다. 각 KISA 항목 안에도 아직 탐지하지 않는 인접한 직접 API가 남아 있어, 실제 검증 가능한 범위만 넓힐 필요가 있다. 다만 Semgrep OSS 1.95.0에는 Java 실제 타입 해석이 없고, 현재 규칙은 함수 매개변수만 source로 둔다. 따라서 타입·프레임워크·sanitizer 해석을 전제하는 범위까지 함께 넓히면 오탐과 지원 범위 과장이 생긴다.

작업 환경에는 원본 요구사항 문서(`docs/원본_요구사항목록.docx`)가 포함되어 있지 않다. 이 결정은 이미 검증된 여섯 KISA 코드의 직접 API 변형만 계획하며, 구현 시작 전 원본 요구사항 문서와 KISA 연결을 다시 대조한다. 이 문서는 구현·검증 증거가 아니며 카탈로그 상태를 바꾸지 않는다.

**Decision**: 고정 Semgrep OSS와 SecScan 자체 작성 `mode: taint` 규칙만 유지한다. 아래 여섯 후보는 기존 규칙의 `pattern-either`에 합치지 않고 각각 독립된 `engine_rule_id`, 취약 fixture, 정상 fixture, provenance를 가진다. 함수 매개변수가 선언한 sink에 직접 도달하는 경우만 대상으로 한다.

| 우선순위 | 예정 규칙 ID | KISA 항목 | 언어 | 선언할 source → sink 범위 | 공개 근거 |
|---|---|---|---|---|---|
| 1 | `secscan.python.pickle-load` | KISA-043 신뢰할 수 없는 데이터의 역직렬화 | Python | 함수 매개변수 → `pickle.load($DATA)` | CWE-502, OWASP A08:2021 |
| 2 | `secscan.python.path-open` | KISA-003 경로 조작 및 자원 삽입 | Python | 함수 매개변수 → `Path($PATH).open(...)` | CWE-22, OWASP A01:2021 |
| 3 | `secscan.javascript.function-constructor` | KISA-002 코드 삽입 | JavaScript | 함수 매개변수 → 한 인자 `Function($CODE)` 생성자 호출 | CWE-95, OWASP A03:2021 |
| 4 | `secscan.javascript.dom-insert-adjacent-html` | KISA-004 크로스사이트 스크립트 | JavaScript | 함수 매개변수 → `$ELEMENT.insertAdjacentHTML($POSITION, $DATA)`의 HTML 인자 | CWE-79, OWASP A03:2021 |
| 5 | `secscan.java.process-builder` | KISA-005 운영체제 명령어 삽입 | Java | 메서드 `String` 매개변수 → `new ProcessBuilder($COMMAND).start()` | CWE-78, OWASP A03:2021 |
| 6 | `secscan.python.subprocess-run-shell` | KISA-005 운영체제 명령어 삽입 | Python | 함수 매개변수 → `subprocess.run($COMMAND, shell=True)` | CWE-78, OWASP A03:2021 |

- `secscan.python.pickle-load`와 `secscan.python.path-open`은 각각 기존 `secscan.python.pickle-loads`, `secscan.python.open-user-path`와 다른 규칙 ID를 사용한다. 이들은 기존 규칙에 패턴을 덧붙이는 변형이 아니라 서로 다른 source-to-sink 계약이다.
- `subprocess`의 이번 범위는 `subprocess.run(..., shell=True)` 한 가지 호출 형식으로 고정한다. `Popen`, `call`, `check_call`, `check_output`, `os.popen`과 셸 문자열 조합은 포함하지 않는다. 이 API들은 같은 규칙의 `pattern-either`로 묶지 않으며, 필요하면 별도 ADR·규칙·fixture로 다시 결정한다.
- `innerHTML +=`는 구현 후보가 아니라 사전 spike 대상이다. 고정 Semgrep OSS에서 복합 대입을 taint sink로 정확히 한 건 매치하고, 같은 규칙의 고정값 정상 fixture가 대상 `check_id` 0건을 내며, 기존 `innerHTML =` 규칙과 중복하지 않는다는 증거가 있어야 한다. 어느 하나라도 불명확하거나 재현되지 않으면 이 변형은 제외한다. spike 통과 뒤에도 ADR과 실행 계획을 갱신하고 일반 전환 게이트를 모두 통과하기 전에는 규칙 YAML, 매핑 시드, 카탈로그 상태에 넣지 않는다.
- Java `Statement.execute(String)`은 후보에서 영구 제외한다. ADR-039의 메서드명 기반 규칙은 실제 `Statement`와 `PreparedStatement` 타입을 구분할 수 없으므로, `execute(String)`을 안전하게 판정할 수 없다.
- `HttpServletRequest`, `@RequestParam`, `req.body`, Flask `request.args` 등 프레임워크 입력 source와 framework별 sanitizer 모델링은 이번 결정에서 제외한다. 이는 직접 API의 작은 변형이 아니라 source 정의와 오탐 정책이 달라지는 새 규칙 종류이며, E7 백로그의 제외 원칙을 따른다.
- Java 역직렬화, ORM/JPA, `Path.open` 외 파일 API, JavaScript 템플릿·JSX·SSR, 간접 호출, 실제 DOM·JDBC 타입 해석, sanitizer·허용 목록 인식은 포함하지 않는다.

각 후보는 다음 전환 게이트를 모두 만족할 때만 구현·매핑한다.

1. 고정 YAML을 `--no-rewrite-rule-ids`와 함께 Semgrep OSS 1.95.0으로 직접 실행했을 때 취약 fixture에서 예정한 접두어 없는 `check_id`가 정확히 한 건 나온다.
2. 같은 sink의 고정값 정상 fixture에서 검증 대상 `check_id`가 0건 나온다. 이는 선언한 형태의 최소 회귀 검증이지, 모든 안전화 전략의 증명은 아니다.
3. `backend/semgrep-rules/secscan-security.yml`, `RULES_PROVENANCE.md`, `KISA_RULE_MAPPING_SEED`, 취약·정상 fixture, E5 실제 Semgrep 정규화 테스트, E5 실행 문서를 같은 변경에서 갱신한다.
4. 집중 테스트와 필터 없는 백엔드 `pytest -q`, Ruff, `git diff --check`, GitHub Actions Ubuntu CI가 통과한다. 결과는 해당 `engine_rule_id`와 기존 KISA 코드로 정규화되어 저장돼야 한다.

모든 후보는 이 게이트를 통과해도 이미 `부분 지원`인 여섯 KISA 코드 안의 직접 API 범위만 넓힌다. `지원` 상태로 올리지 않으며, 규칙 수나 향후 탐지 항목 수의 상한도 정하지 않는다.

**Alternatives**: 현재 아홉 규칙만 유지, 기존 규칙에 `pattern-either`로 API 변형을 추가, `Statement.execute(String)`을 이름만으로 추가, `subprocess` API군을 한 규칙으로 통합, 프레임워크 source를 같은 작업에 포함, 공식 또는 제3자 Semgrep 규칙 사용

**Consequences**: 규칙 단위의 설명·fixture·매핑이 늘어 실제 탐지 경로를 더 정확히 보여 줄 수 있다. 반면 여섯 규칙의 provenance 작성과 회귀 검증 비용도 늘어난다. 타입·프레임워크 해석이 필요한 요구가 생기면 이 ADR을 확장하지 않고 source 모델, sanitizer 정책, 오탐 허용 기준을 별도 ADR로 결정해야 한다. 스키마·마이그레이션·새 API는 추가하지 않는다.

**References**: ADR-011, ADR-023, ADR-030, ADR-032, ADR-036, ADR-039, ADR-040, `docs/epic/e5-result-normalization.md` E5-10, `docs/epic/e7-sast-evaluation-plan.md`, SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
