# ADR-041: 기존 6개 KISA 항목의 직접 API 탐지 범위 확장

**Context**: ADR-039와 ADR-040까지 구현·검증된 자체 Semgrep 규칙은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043 여섯 항목을 제한된 문법적 source-to-sink 형태로 `부분 지원`한다. 각 KISA 항목 안에도 아직 탐지하지 않는 인접한 직접 API가 남아 있어, 실제 검증 가능한 범위만 넓힐 필요가 있다. 다만 Semgrep OSS 1.95.0에는 Java 실제 타입 해석이 없고, 현재 규칙은 함수 매개변수만 source로 둔다. 따라서 타입·프레임워크·sanitizer 해석을 전제하는 범위까지 함께 넓히면 오탐과 지원 범위 과장이 생긴다.

2026-09-02에 원본 요구사항 문서를 대조했다. SFR-010~014, TST-004~006, QLT-002~004는 Java·JavaScript·Python의 확장 가능한 진단, KISA 49개 카탈로그, 항목별 독립 시험, 공통 결과 모델을 요구한다. 원문은 특정 KISA 코드, API 변형, 규칙 수 또는 `지원` 상태를 고정하지 않으므로, 이 결정은 ADR-011·ADR-039·ADR-040에서 검증한 여섯 기존 KISA 코드의 직접 API 변형만 계획한다. 이 문서는 구현·검증 증거가 아니며 카탈로그 상태를 바꾸지 않는다.

**Decision**: 고정 Semgrep OSS와 SecScan 자체 작성 `mode: taint` 규칙만 유지한다. 아래 여섯 후보는 기존 규칙에 sink를 합치지 않고 각각 독립된 `engine_rule_id`, 취약 fixture, 정상 fixture, provenance를 가진다. 같은 API의 문법 형태만 다른 `Function(...)`·`new Function(...)`은 하나의 규칙 안에서 `pattern-either`로 함께 다룬다. 함수 또는 메서드 매개변수에서 선언한 sink로 흐르는 경우를 대상으로 하며, 고정 엔진의 재현 가능한 별칭·상수 전파·중간값 전파는 아래에 명시한 범위로 포함한다.

| 우선순위 | 예정 규칙 ID | KISA 항목 | 언어 | 선언할 source → sink 범위 | 공개 근거 |
|---|---|---|---|---|---|
| 1 | `secscan.python.pickle-load` | KISA-043 신뢰할 수 없는 데이터의 역직렬화 | Python | 함수 매개변수 → `pickle.load($DATA)`; 직접 file-like 객체, `io.BytesIO` 래핑, `open()` 뒤 변수 재대입을 포함 | CWE-502, OWASP A08:2021 |
| 2 | `secscan.python.path-open` | KISA-003 경로 조작 및 자원 삽입 | Python | 함수 매개변수 → `Path($PATH).open(...)` | CWE-22, OWASP A01:2021 |
| 3 | `secscan.javascript.function-constructor` | KISA-002 코드 삽입 | JavaScript | 함수 매개변수 → 한 인자 `Function($CODE)` 또는 `new Function($CODE)` | CWE-95, OWASP A03:2021 |
| 4 | `secscan.javascript.dom-insert-adjacent-html` | KISA-004 크로스사이트 스크립트 | JavaScript | 함수 매개변수 → `$ELEMENT.insertAdjacentHTML($POSITION, $DATA)`의 HTML 인자; 템플릿 문자열 보간을 포함 | CWE-79, OWASP A03:2021 |
| 5 | `secscan.java.process-builder` | KISA-005 운영체제 명령어 삽입 | Java | 접근 제어자·static 여부와 무관한 메서드 `String` 매개변수 → `new ProcessBuilder($COMMAND).start()` | CWE-78, OWASP A03:2021 |
| 6 | `secscan.python.subprocess-run-shell` | KISA-005 운영체제 명령어 삽입 | Python | `subprocess.run($COMMAND, shell=True)`; import 별칭·from-import, 추가 고정 kwargs, 지역 상수 `True` 전파를 포함 | CWE-78, OWASP A03:2021 |

- `secscan.python.pickle-load`와 `secscan.python.path-open`은 각각 기존 `secscan.python.pickle-loads`, `secscan.python.open-user-path`와 다른 규칙 ID를 사용한다. 이들은 기존 규칙에 패턴을 덧붙이는 변형이 아니라 서로 다른 source-to-sink 계약이다.
- `secscan.python.pickle-load`은 고정 엔진의 taint 전파에 따라 함수 매개변수가 `io.BytesIO(...)`로 감싸지거나 `f = open($PATH, ...)`로 재대입된 뒤 `pickle.load(f)`에 이르는 경우도 탐지한다. 후자는 기존 `secscan.python.open-user-path`과 같은 파일에서 함께 발생할 수 있다. 이는 서로 다른 sink 줄, `engine_rule_id`, KISA 코드(KISA-003·KISA-043), 지문을 가진 별도 Finding이지 중복이 아니다. 취약 fixture의 “한 건” 게이트는 전체 규칙 집합의 총 결과가 아니라 검증 대상 규칙의 `check_id` 한 건을 뜻한다.
- `secscan.python.path-open`의 초기 계약은 함수 매개변수 → 단일 인자 `Path($PATH).open(...)`으로 고정한다. 2026-09-02 고정 Semgrep OSS 1.95.0 spike에서 이 형태는 취약 fixture 1건, 고정 경로 정상 fixture 0건, 기존 `secscan.python.open-user-path`과 중복 0건을 냈다. 변수 분리, 다중 인자 `Path`, `.resolve()`·`.joinpath()`, `pathlib.Path(...)` 완전 수식 호출, `Path` import 별칭, `os.open`, `shutil`은 의도적으로 제외한다. 이 변형들은 향후 별도 규칙·fixture·PR로만 검토한다.
- `secscan.javascript.function-constructor`은 같은 동적 함수 생성 API의 두 AST 형태를 하나의 규칙 ID 안에서 `pattern-either`로 다룬다. 두 인자 이상인 `Function("arg", $CODE)`과 `new Function("arg", $CODE)`은 포함하지 않는다.
- `secscan.javascript.dom-insert-adjacent-html`은 두 번째 HTML 인자로 흐르는 값만 본다. 위치 인자가 사용자 입력이고 HTML이 고정값인 경우는 제외하지만, HTML 템플릿 문자열의 사용자 입력 보간은 포함한다.
- `secscan.java.process-builder`은 public·protected·package-private·private 및 static·인스턴스 메서드를 모두 포함한다. 다중 인자 생성자, `"sh", "-c", $COMMAND`, 변수에 담은 `ProcessBuilder`의 뒤늦은 `start()`, `Runtime.exec`은 포함하지 않는다.
- `subprocess`의 이번 범위는 `run` API와 셸 실행이 확정된 형태로 고정한다. `import subprocess as sp`·`from subprocess import run` 결합, 추가 고정 kwargs, `shell_flag = True` 같은 지역 상수 전파는 포함한다. `shell=False`, 상수로 접히지 않는 동적 shell 값, `Popen`, `call`, `check_call`, `check_output`, `os.popen`과 셸 문자열 조합은 포함하지 않는다. `Popen` 등은 같은 규칙의 `pattern-either`로 묶지 않으며, 필요하면 별도 ADR·규칙·fixture로 다시 결정한다.
- `innerHTML +=` 사전 spike는 2026-09-02에 결론 났다. 전용 후보 규칙은 취약 fixture 1건과 고정값 정상 fixture 0건을 냈지만, 기존 `secscan.javascript.dom-innerhtml`도 같은 `+=` fixture를 이미 한 건 탐지해 두 규칙을 함께 실행하면 두 건이 됐다. 고정 엔진이 `=` 패턴을 복합 대입에도 적용하므로 `+=` 전용 `engine_rule_id`는 추가하지 않는다. 이는 탐지 공백이 아니라 기존 규칙과 분리할 수 없는 엔진 동작이며, 새 매핑·상태·확장 PR의 대상이 아니다. 기존 규칙의 회귀 fixture와 provenance에는 이 실제 동작을 반영한다.
- Java `Statement.execute(String)`은 후보에서 영구 제외한다. ADR-039의 메서드명 기반 규칙은 실제 `Statement`와 `PreparedStatement` 타입을 구분할 수 없으므로, `execute(String)`을 안전하게 판정할 수 없다.
- `HttpServletRequest`, `@RequestParam`, `req.body`, Flask `request.args` 등 프레임워크 입력 source와 framework별 sanitizer 모델링은 이번 결정에서 제외한다. 이는 직접 API의 작은 변형이 아니라 source 정의와 오탐 정책이 달라지는 새 규칙 종류이며, E7 백로그의 제외 원칙을 따른다.
- Java 역직렬화, ORM/JPA, `Path.open` 외 파일 API, React·JSX·프레임워크 템플릿·SSR, 간접 호출, 실제 DOM·JDBC 타입 해석, sanitizer·허용 목록 인식은 포함하지 않는다. 직접 `insertAdjacentHTML` 호출의 일반 JavaScript 템플릿 문자열 보간은 이 제외와 다르며 위 선언 범위에 포함한다.

각 후보는 다음 전환 게이트를 모두 만족할 때만 구현·매핑한다.

1. 고정 YAML을 `--no-rewrite-rule-ids`와 함께 Semgrep OSS 1.95.0으로 직접 실행했을 때 취약 fixture에서 검증 대상 예정 `check_id`가 정확히 한 건 나온다. 같은 파일의 다른 위험 sink가 다른 규칙으로 추가 Finding을 내는 경우는 결과 ID·줄·KISA 매핑을 독립적으로 기대값에 기록한다.
2. 같은 sink의 고정값 정상 fixture에서 검증 대상 `check_id`가 0건 나온다. 이는 선언한 형태의 최소 회귀 검증이지, 모든 안전화 전략의 증명은 아니다.
3. `backend/semgrep-rules/secscan-security.yml`, `RULES_PROVENANCE.md`, `KISA_RULE_MAPPING_SEED`, 취약·정상 fixture, E5 실제 Semgrep 정규화 테스트, E5 실행 문서를 같은 변경에서 갱신한다.
4. 집중 테스트와 필터 없는 백엔드 `pytest -q`, Ruff, `git diff --check`, GitHub Actions Ubuntu CI가 통과한다. 결과는 해당 `engine_rule_id`와 기존 KISA 코드로 정규화되어 저장돼야 한다.

모든 후보는 이 게이트를 통과해도 이미 `부분 지원`인 여섯 KISA 코드 안의 직접 API 범위만 넓힌다. `지원` 상태로 올리지 않으며, 규칙 수나 향후 탐지 항목 수의 상한도 정하지 않는다.

**Alternatives**: 현재 아홉 규칙만 유지, 기존 규칙에 `pattern-either`로 API 변형을 추가, `Statement.execute(String)`을 이름만으로 추가, `subprocess` API군을 한 규칙으로 통합, 프레임워크 source를 같은 작업에 포함, 공식 또는 제3자 Semgrep 규칙 사용

**Consequences**: 규칙 단위의 설명·fixture·매핑이 늘어 실제 탐지 경로를 더 정확히 보여 줄 수 있다. 반면 여섯 규칙의 provenance 작성과 회귀 검증 비용도 늘어난다. 타입·프레임워크 해석이 필요한 요구가 생기면 이 ADR을 확장하지 않고 source 모델, sanitizer 정책, 오탐 허용 기준을 별도 ADR로 결정해야 한다. 스키마·마이그레이션·새 API는 추가하지 않는다.

**References**: ADR-011, ADR-023, ADR-030, ADR-032, ADR-036, ADR-039, ADR-040, `docs/epic/e5-result-normalization.md` E5-10, `docs/epic/e7-sast-evaluation-plan.md`, SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
