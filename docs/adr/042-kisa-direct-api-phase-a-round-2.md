# ADR-042: 기존 6개 KISA 항목의 직접 API A단계 2차 확장

**Context**: PR #52가 ADR-041의 여섯 직접 API 규칙을 구현·Ubuntu CI 검증까지 마쳤다. SecScan은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043을 제한된 자체 Semgrep 규칙으로 계속 `부분 지원`한다. 원본 요구사항의 SFR-010~014, TST-004~006, QLT-002~004는 다언어 정적 분석의 확장성, KISA 49개 카탈로그, 항목별 독립 검증과 공통 결과 모델을 요구하지만, 특정 API·규칙 수·지원 상태를 정하지 않는다.

이번 라운드는 ADR-041이 남긴 직접 API와 같은 source 모델 안의 인접 sink를 사전 spike로 검토한다. 고정 Semgrep OSS 1.95.0은 함수 매개변수에서 별칭·상수·래핑·재대입을 거친 taint를 재현 가능하게 전파할 수 있지만, Java 실제 타입, JavaScript callback의 문자열 여부, framework request source, sanitizer·허용 목록은 해석하지 않는다. 이 한계를 직접 API 확장과 섞으면 오탐·미탐 범위를 정직하게 설명할 수 없다.

**Decision**: 이번 A단계는 함수·비동기 함수·Java 메서드 매개변수만 source로 유지하고, 기존 여섯 KISA 코드 안의 아래 직접 sink만 구현 후보로 둔다. 각 행은 spike에서 취약 fixture의 대상 `check_id` 1건, 고정값 정상·선언한 제외 fixture의 대상 `check_id` 0건, production 규칙과 같은 sink 줄의 중복 0건을 확인했다. 구현 PR에서도 실제 fixture로 같은 검증을 다시 수행한다.

| 처리 | 규칙 ID | KISA | source → sink 범위 | 근거 |
|---|---|---|---|---|
| 신규 | `secscan.javascript.dom-outerhtml` | KISA-004 | JavaScript 함수 매개변수 → `$ELEMENT.outerHTML = $DATA` 또는 `+= $DATA`의 RHS | CWE-79, OWASP Top 10 2021 A03 |
| 신규 | `secscan.javascript.document-write` | KISA-004 | JavaScript 함수 매개변수 → `document.write($DATA)` 또는 `document.writeln($DATA)` | CWE-79, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.pickle-unpickler-load` | KISA-043 | Python 함수·비동기 함수 매개변수 → `pickle.Unpickler($DATA).load()` | CWE-502, OWASP Top 10 2021 A08 |
| 신규 | `secscan.python.subprocess-popen-shell` | KISA-005 | Python 함수·비동기 함수 매개변수 → `subprocess.Popen($COMMAND, ..., shell=True, ...)` | CWE-78, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.subprocess-call-shell` | KISA-005 | Python 함수·비동기 함수 매개변수 → `subprocess.call($COMMAND, ..., shell=True, ...)` | CWE-78, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.subprocess-check-call-shell` | KISA-005 | Python 함수·비동기 함수 매개변수 → `subprocess.check_call($COMMAND, ..., shell=True, ...)` | CWE-78, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.subprocess-check-output-shell` | KISA-005 | Python 함수·비동기 함수 매개변수 → `subprocess.check_output($COMMAND, ..., shell=True, ...)` | CWE-78, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.os-popen` | KISA-005 | Python 함수·비동기 함수 매개변수 → `os.popen($COMMAND)` | CWE-78, OWASP Top 10 2021 A03 |
| 신규 | `secscan.python.subprocess-output-shell` | KISA-005 | Python 함수·비동기 함수 매개변수 → `subprocess.getoutput($COMMAND)` 또는 `subprocess.getstatusoutput($COMMAND)` | CWE-78, OWASP Top 10 2021 A03 |
| 기존 ID 확장 | `secscan.javascript.function-constructor` | KISA-002 | `Function(...)`·`new Function(...)`의 마지막 함수 본문 인자만 tainted인 다중 인자 호출 | CWE-95, OWASP Top 10 2021 A03 |
| 기존 ID 확장 | `secscan.java.jdbc-statement-sql` | KISA-001 | Java `String` 매개변수 → `executeLargeUpdate(String)` | CWE-89, OWASP Top 10 2021 A03 |
| 기존 ID 확장 | `secscan.python.path-open` | KISA-003 | `Path.open()`의 `pathlib.Path` 완전 수식·import 별칭·다중 인자·`joinpath`·`resolve`·변수 분리 형태 | CWE-22, OWASP Top 10 2021 A01 |
| 기존 ID 확장 | `secscan.java.process-builder` | KISA-005 | `ProcessBuilder builder = new ProcessBuilder(command); builder.start()`처럼 같은 지역 변수에 결합된 변수 분리 형태 | CWE-78, OWASP Top 10 2021 A03 |

규칙 ID는 기본적으로 서로 다른 함수·메서드 이름마다 분리한다. 이는 `eval`과 `exec`을 독립 규칙으로 둔 ADR-040의 원칙을 따른다. 다만 아래는 같은 위험 sink의 근접 문법으로 예외적으로 한 ID의 `pattern-either`로 묶는다.

- `document.write`와 `document.writeln`: 같은 `document` 스트림 쓰기이며 후자는 줄바꿈만 추가한다.
- `subprocess.getoutput`과 `subprocess.getstatusoutput`: 같은 암묵적 셸 출력 실행 계열이며 반환 형식만 다르다.
- 기존 `secscan.java.jdbc-statement-sql`의 `executeQuery`, `executeUpdate`, `executeLargeUpdate`: `String` SQL 실행이라는 같은 JDBC Statement sink 계열이다.
- 기존 `secscan.javascript.function-constructor`의 호출·`new` AST와 기존 `secscan.python.path-open`의 import·경로 표현식 변형: 각각 같은 Function 생성자와 같은 Path file-open sink다.

고정 엔진이 실제로 발견하는 별칭, import 별칭, 지역 상수, wrapper, 재대입 전파는 취약 흐름으로 받아들이며, literal 문법만 허용한다고 거짓으로 문서화하지 않는다. 반대로 변수 분리 `Path.open`과 `ProcessBuilder.start`는 새 `pattern-inside` 결합 방식이므로, 단일 표현식 변형과 별도 fixture 묶음으로 검증한다. 관련 없는 `conn.open()`·`worker.start()`과 재대입 뒤의 신뢰된 객체가 탐지되지 않아야 한다.

다음은 사전 spike 결과에 따라 이번 A단계에서 제외한다.

- JavaScript 문자열 `setTimeout`·`setInterval`: 함수 매개변수가 문자열인지 callback인지 타입을 구분하지 못해 정상 `setTimeout(callback, delay)` 전달을 탐지한다.
- Java `Statement.addBatch(String)`: SQL을 실행하지 않고 큐에 추가할 뿐이며, 나중의 무인자 `executeBatch()`와 결합하지 않는 단일 sink Finding은 현재 직접 실행 계약과 다르다.
- Java `Statement.execute(String)`: ADR-041의 결론대로 `Statement`와 `PreparedStatement`의 실제 타입을 구분할 수 없다.
- `Runtime.exec`의 다른 문법: 새 sink가 아니라 기존 `secscan.java.runtime-exec`의 정상 회귀 fixture로만 검증한다.
- `Path.read_text/read_bytes/write_text/write_bytes`: `Path.open`과 다른 파일 I/O API이므로 KISA 범위·source-to-sink 계약을 이번 spike에서 확정하지 않았다.
- Java 역직렬화, ORM/JPA, React·JSX·SSR·간접 호출, framework request source, sanitizer·허용 목록 인식: 직접 API A단계의 범위를 넘으므로 제외한다.

**Consequences**: 통과한 신규 sink에는 각각 KISA 매핑, provenance, 취약·정상·제외 fixture, E5 정규화 테스트가 추가된다. 기존 ID 확장은 새 매핑 행을 만들지 않지만, 기존 provenance·fixture·테스트의 선언 범위를 함께 넓힌다. `Path.open` 변수 분리와 `ProcessBuilder` 변수 분리는 고정 엔진의 `pattern-inside` metavariable 결합에 의존하므로, 구현에서 shadowed 변수명·여러 후보 객체·재대입 순서를 포함한 회귀 fixture를 추가한다. 어떤 후보도 KISA 상태를 `지원`으로 올리지 않으며, 규칙 수 또는 이후 확장 수의 상한을 만들지 않는다.

프레임워크 요청 객체를 source로 인식하는 B단계는 A단계의 sink 정의를 재사용할 수 있지만, source·sanitizer·오탐 정책을 별도 ADR로 결정한 뒤에만 시작한다. 스키마, 마이그레이션, 사용자 API는 이번 문서화·구현 범위에 포함하지 않는다.

**Alternatives**: PR #52의 규칙 범위 유지, subprocess API군을 한 규칙 ID로 통합, `setTimeout`·`setInterval`을 타입 없이 추가, `addBatch`를 실행 sink로 취급, 모든 Path file I/O API를 함께 추가, framework source를 같은 라운드에 포함, 공식 또는 제3자 Semgrep 규칙 도입

**References**: ADR-011, ADR-023, ADR-030, ADR-039, ADR-040, ADR-041, `docs/epic/e5-result-normalization.md` E5-10, `docs/epic/e5-kisa-six-code-coverage-expansion.md`, SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
