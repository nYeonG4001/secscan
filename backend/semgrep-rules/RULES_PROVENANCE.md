# SecScan 자체 규칙 출처

이 디렉터리의 규칙은 SecScan이 독자 작성한 규칙이다. Semgrep 공식 규칙이나 다른 제3자
Semgrep 규칙의 패턴·로직을 복사하거나 변형하지 않았다. 규칙 변경은 근거 검토와 예상 결과
테스트 갱신을 포함한 별도 PR로 진행한다.

| 규칙 `id` | 언어 | 공개 보안 근거 | 작성·변경 사유 |
|---|---|---|---|
| `secscan.java.runtime-exec` | Java | CWE-78, OWASP Top 10 2021 A03 | 운영체제 명령 주입 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.javascript.eval` | JavaScript | CWE-95, OWASP Top 10 2021 A03 | 문자열 코드 실행 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.python.pickle-loads` | Python | CWE-502, OWASP Top 10 2021 A08 | 신뢰할 수 없는 역직렬화 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.java.jdbc-statement-sql` | Java | CWE-89, OWASP Top 10 2021 A03 | 메서드 `String` 매개변수가 JDBC 문자열 SQL 실행으로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.javascript.dom-innerhtml` | JavaScript | CWE-79, OWASP Top 10 2021 A03 | 함수 매개변수의 DOM `innerHTML` 직접 대입 형태를 탐지하기 위해 추가 |
| `secscan.python.open-user-path` | Python | CWE-22, OWASP Top 10 2021 A01 | 함수 매개변수가 내장 `open()` 경로로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.os-system` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `os.system()`으로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.eval` | Python | CWE-95, OWASP Top 10 2021 A03 | 함수 매개변수가 bare `eval()` 이름 호출로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.exec` | Python | CWE-95, OWASP Top 10 2021 A03 | 함수 매개변수가 bare `exec()` 이름 호출로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.pickle-load` | Python | CWE-502, OWASP Top 10 2021 A08 | 함수 매개변수가 `pickle.load()`로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.path-open` | Python | CWE-22, OWASP Top 10 2021 A01 | 함수 매개변수가 단일 인자 `Path().open()`로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.javascript.function-constructor` | JavaScript | CWE-95, OWASP Top 10 2021 A03 | 함수 매개변수가 한 인자 `Function()` 또는 `new Function()`으로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.javascript.dom-insert-adjacent-html` | JavaScript | CWE-79, OWASP Top 10 2021 A03 | 함수 매개변수가 `insertAdjacentHTML()`의 HTML 인자로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.java.process-builder` | Java | CWE-78, OWASP Top 10 2021 A03 | 메서드 `String` 매개변수가 단일 인자 `ProcessBuilder` 생성 후 즉시 `start()`로 흐르는 제한된 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-run-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.run(shell=True)`로 흐르는 제한된 형태를 탐지하기 위해 추가 |

E5는 `secscan-security.yml` 파일을 `--config`로 직접 지정하고
`--no-rewrite-rule-ids`를 함께 사용한다. Semgrep OSS 1.95.0 실제 출력에서 위 `id`와 같은
접두어 없는 `check_id`를 확인했으며, 이를 고정 `engine_rule_id`와 매핑 시드에 사용한다.

- Java 규칙은 메서드의 `String` 매개변수가 `Runtime.getRuntime().exec(...)`로 흐르는 경우를 다룬다.
- JavaScript 규칙은 함수 매개변수가 `eval(...)`로 흐르는 경우를 다룬다.
- Python 규칙은 함수 매개변수가 `pickle.loads(...)`로 흐르는 경우를 다룬다.
- Java SQL 규칙은 접근 제한자와 `static` 여부에 관계없이 메서드의 `String` 매개변수가 인자 하나인 `executeQuery(String)` 또는 `executeUpdate(String)`으로 흐르는 경우만 다룬다. 메서드명만으로 sink를 판정하므로 실제 JDBC 타입은 해석하지 않으며, 한 인자를 받는 동명 `PreparedStatement` 호출도 이 제한된 범위에 포함한다. 바인딩 뒤 인자 없이 호출하는 `PreparedStatement.executeQuery()`/`executeUpdate()`, `execute(String)`, `executeUpdate(String, int)`, ORM, JPA는 포함하지 않는다.
- JavaScript DOM XSS 규칙은 선언·익명·async 함수, 블록·표현식 본문 화살표 함수, 클래스 메서드와 동기 객체 메서드의 단순 식별자 매개변수가 `$ELEMENT.innerHTML = $DATA`에 직접 대입되는 경우만 다룬다. 속성명만으로 sink를 판정하며, `innerHTML +=`, `insertAdjacentHTML`, React·템플릿·SSR·프레임워크 sanitizer, async 객체 축약 메서드와 기본값·구조 분해·generator 매개변수는 포함하지 않는다.
- Python 경로 조작 규칙은 동기·비동기 함수 매개변수가 bare builtin `open($PATH, ...)`로 흐르는 경우만 다룬다. `Path.open`, `os.open`, `shutil`, 압축 해제, 업로드 경로 검증은 포함하지 않으며, 로컬 `open` 재정의는 구분하지 않는다.
- Python 운영체제 명령어 삽입 규칙은 `import os`가 있는 파일에서 동기 함수 매개변수가 `os.system($COMMAND)`으로 직접 흐르는 경우만 다룬다. `subprocess.run`, `subprocess.Popen`, `os.popen`, 셸 문자열 조합의 변형은 포함하지 않는다. 이름 해석은 하지 않으므로 로컬에서 재정의한 `os` 이름은 구분하지 않는다.
- Python 코드 삽입 규칙은 동기 함수 매개변수가 `eval($CODE)` 또는 `exec($CODE)` 이름 호출로 직접 흐르는 경우를 각각 독립적으로 다룬다. sanitizer·허용 목록, 간접 호출과 framework별 입력 추적은 포함하지 않으며, 이름 해석은 하지 않으므로 로컬에서 재정의한 `eval`·`exec` 이름도 구분하지 않는다.

- Python `pickle.load` 역직렬화 규칙은 동기·비동기 함수 매개변수가 `pickle.load($DATA)`로 흐르는 경우를 다룬다. 직접 file-like 객체 전달, `io.BytesIO()` 래핑, 사용자 경로 → `open()` → `pickle.load()` 전파를 포함한다. 마지막 형태는 같은 파일에서 `secscan.python.open-user-path`(KISA-003)와 함께 발생할 수 있으며, 서로 다른 sink 줄·규칙 ID·KISA 코드를 가진 별도 Finding이다. 기존 `secscan.python.pickle-loads`(`pickle.loads`)와는 다른 sink이므로 별도 규칙 ID를 사용한다. `yaml.load`, `marshal`, `shelve` 등 다른 역직렬화 API는 포함하지 않는다.
- Python `Path.open` 경로 조작 규칙은 동기·비동기 함수 매개변수가 단일 인자 `Path($PATH).open(...)`로 흐르는 경우만 다룬다. 변수에 `Path` 객체를 먼저 담은 뒤 `.open()`을 호출하는 분리 형태, 다중 인자 `Path("/safe", user_path)`, `.resolve()`·`.joinpath()` 체인, `pathlib.Path(...)` 완전 수식 호출, `Path` import 별칭, `os.open`, `shutil`은 의도적으로 제외한다. 기존 `secscan.python.open-user-path`(bare `open()`)와는 다른 호출자·sink이므로 별도 규칙 ID를 사용한다.
- JavaScript `Function` 생성자 코드 삽입 규칙은 함수 매개변수가 한 인자 `Function($CODE)` 또는 `new Function($CODE)`으로 흐르는 경우를 하나의 규칙 ID 안에서 `pattern-either`로 다룬다. 두 인자 이상인 `Function("arg", $CODE)`과 `new Function("arg", $CODE)`은 포함하지 않는다. 기존 `secscan.javascript.eval`(`eval()`)과는 다른 실행 API이므로 별도 규칙 ID를 사용한다.
- JavaScript `insertAdjacentHTML` XSS 규칙은 함수 매개변수가 `$ELEMENT.insertAdjacentHTML($POSITION, $DATA)`의 두 번째 HTML 인자(`$DATA`)로 흐르는 경우만 다룬다. 일반 JavaScript 템플릿 문자열 보간을 포함한다. 위치 인자(`$POSITION`)가 사용자 입력이고 HTML이 고정값인 경우는 `focus-metavariable: $DATA`로 제외한다. `innerHTML`, JSX, React·프레임워크 템플릿·SSR source는 포함하지 않는다. 속성명만으로 sink를 판정하며, 실제 DOM 객체 타입은 해석하지 않는다.
- Java `ProcessBuilder` 운영체제 명령어 삽입 규칙은 접근 제어자(public, protected, private, package-private)와 static 여부에 관계없이 메서드의 `String` 매개변수가 `new ProcessBuilder($COMMAND).start()`로 흐르는 경우를 다룬다. 다중 인자 생성자(`new ProcessBuilder("sh", "-c", command)`), 변수에 `ProcessBuilder`를 먼저 담은 뒤 `start()`를 호출하는 분리 형태, `Runtime.exec`은 포함하지 않는다. 기존 `secscan.java.runtime-exec`과는 다른 프로세스 생성 API이므로 별도 규칙 ID를 사용한다.
- Python `subprocess.run` 운영체제 명령어 삽입 규칙은 동기·비동기 함수 매개변수가 `subprocess.run($COMMAND, shell=True)`로 흐르는 경우를 다룬다. `import subprocess as sp`(별칭)와 `from subprocess import run`(from-import) 결합, 추가 고정 kwargs(`capture_output=True` 등), `shell_flag = True` 같은 지역 상수 `True` 전파를 포함한다. `shell=False`, 상수로 접히지 않는 동적 shell 값, `subprocess.Popen`, `subprocess.call`, `subprocess.check_call`, `subprocess.check_output`, `os.popen`은 포함하지 않는다. 기존 `secscan.python.os-system`과는 다른 API와 `shell=True` 제약이므로 별도 규칙 ID를 사용한다.
- `secscan.javascript.dom-innerhtml` 규칙은 고정 Semgrep OSS 1.95.0에서 `$ELEMENT.innerHTML = $DATA` 패턴이 `innerHTML +=` 복합 대입도 같은 규칙 ID로 탐지하는 실제 동작을 확인했다. `+=` 전용 규칙 ID·KISA 매핑은 추가하지 않으며, 회귀 fixture로 이 동작을 검증한다.

이 규칙들은 각 언어와 API의 제한된 source-to-sink 형태만 다루며, 모든 프레임워크나 변형을
포괄한다고 주장하지 않는다.
