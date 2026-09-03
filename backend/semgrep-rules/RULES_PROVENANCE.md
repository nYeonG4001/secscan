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
| `secscan.javascript.dom-outerhtml` | JavaScript | CWE-79, OWASP Top 10 2021 A03 | 함수 매개변수의 DOM `outerHTML` 직접 대입 형태를 탐지하기 위해 추가 |
| `secscan.javascript.document-write` | JavaScript | CWE-79, OWASP Top 10 2021 A03 | 함수 매개변수가 `document.write`/`document.writeln`으로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.pickle-unpickler-load` | Python | CWE-502, OWASP Top 10 2021 A08 | 함수 매개변수가 `pickle.Unpickler(file).load()`로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-popen-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.Popen(shell=True)`로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-call-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.call(shell=True)`로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-check-call-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.check_call(shell=True)`로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-check-output-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.check_output(shell=True)`로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.os-popen` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `os.popen()`으로 흐르는 형태를 탐지하기 위해 추가 |
| `secscan.python.subprocess-output-shell` | Python | CWE-78, OWASP Top 10 2021 A03 | 함수 매개변수가 `subprocess.getoutput`/`subprocess.getstatusoutput`으로 흐르는 형태를 탐지하기 위해 추가 |

E5는 `secscan-security.yml` 파일을 `--config`로 직접 지정하고
`--no-rewrite-rule-ids`를 함께 사용한다. Semgrep OSS 1.95.0 실제 출력에서 위 `id`와 같은
접두어 없는 `check_id`를 확인했으며, 이를 고정 `engine_rule_id`와 매핑 시드에 사용한다.

- Java 규칙은 메서드의 `String` 매개변수가 `Runtime.getRuntime().exec(...)`로 흐르는 경우를 다룬다. `Runtime.getRuntime()`을 변수에 먼저 담은 뒤 그 변수로 `.exec(...)`를 호출하는 분리 형태는 spike에서 확인한 대로 이번 라운드에도 sink로 확장하지 않으며, 회귀 fixture로 계속 탐지되지 않음을 검증한다.
- JavaScript 규칙은 함수 매개변수가 `eval(...)`로 흐르는 경우를 다룬다.
- Python 규칙은 함수 매개변수가 `pickle.loads(...)`로 흐르는 경우를 다룬다.
- Java SQL 규칙은 접근 제한자와 `static` 여부에 관계없이 메서드의 `String` 매개변수가 인자 하나인 `executeQuery(String)`, `executeUpdate(String)` 또는 `executeLargeUpdate(String)`으로 흐르는 경우만 다룬다. 세 메서드는 같은 JDBC `Statement` 문자열 SQL 실행 계열이므로 한 규칙 ID의 `pattern-either`로 함께 다룬다. 메서드명만으로 sink를 판정하므로 실제 JDBC 타입은 해석하지 않으며, 한 인자를 받는 동명 `PreparedStatement` 호출도 이 제한된 범위에 포함한다. 바인딩 뒤 인자 없이 호출하는 `PreparedStatement.executeQuery()`/`executeUpdate()`, `executeUpdate(String, int)`, ORM, JPA는 포함하지 않는다. `Statement.execute(String)`은 `Statement`와 `PreparedStatement`의 실제 타입을 구분할 수 없어 계속 제외하며, `Statement.addBatch(String)`은 호출 시점에 SQL을 실행하지 않고 큐에 추가할 뿐이므로 제외한다. 두 제외는 회귀 fixture로 검증한다.
- JavaScript DOM XSS 규칙은 선언·익명·async 함수, 블록·표현식 본문 화살표 함수, 클래스 메서드와 동기 객체 메서드의 단순 식별자 매개변수가 `$ELEMENT.innerHTML = $DATA`에 직접 대입되는 경우만 다룬다. 속성명만으로 sink를 판정하며, `innerHTML +=`, `insertAdjacentHTML`, React·템플릿·SSR·프레임워크 sanitizer, async 객체 축약 메서드와 기본값·구조 분해·generator 매개변수는 포함하지 않는다.
- Python 경로 조작 규칙은 동기·비동기 함수 매개변수가 bare builtin `open($PATH, ...)`로 흐르는 경우만 다룬다. `Path.open`, `os.open`, `shutil`, 압축 해제, 업로드 경로 검증은 포함하지 않으며, 로컬 `open` 재정의는 구분하지 않는다.
- Python 운영체제 명령어 삽입 규칙은 `import os`가 있는 파일에서 동기 함수 매개변수가 `os.system($COMMAND)`으로 직접 흐르는 경우만 다룬다. `subprocess.run`, `subprocess.Popen`, `os.popen`, 셸 문자열 조합의 변형은 포함하지 않는다. 이름 해석은 하지 않으므로 로컬에서 재정의한 `os` 이름은 구분하지 않는다.
- Python 코드 삽입 규칙은 동기 함수 매개변수가 `eval($CODE)` 또는 `exec($CODE)` 이름 호출로 직접 흐르는 경우를 각각 독립적으로 다룬다. sanitizer·허용 목록, 간접 호출과 framework별 입력 추적은 포함하지 않으며, 이름 해석은 하지 않으므로 로컬에서 재정의한 `eval`·`exec` 이름도 구분하지 않는다.

- Python `pickle.load` 역직렬화 규칙은 동기·비동기 함수 매개변수가 `pickle.load($DATA)`로 흐르는 경우를 다룬다. 직접 file-like 객체 전달, `io.BytesIO()` 래핑, 사용자 경로 → `open()` → `pickle.load()` 전파를 포함한다. 마지막 형태는 같은 파일에서 `secscan.python.open-user-path`(KISA-003)와 함께 발생할 수 있으며, 서로 다른 sink 줄·규칙 ID·KISA 코드를 가진 별도 Finding이다. 기존 `secscan.python.pickle-loads`(`pickle.loads`)와는 다른 sink이므로 별도 규칙 ID를 사용한다. `yaml.load`, `marshal`, `shelve` 등 다른 역직렬화 API는 포함하지 않는다.
- Python `Path.open` 경로 조작 규칙은 동기·비동기 함수 매개변수가 `Path(..., $PATH).open(...)` 형태로 흐르는 경우를 다룬다. 단일 인자와 다중 인자(`Path("/safe", user_path)`, 마지막 인자만 taint 판정), `pathlib.Path(...)` 완전 수식 호출, `.joinpath(...)`·`.resolve()` 체인을 표현식 변형으로 함께 다룬다. `from pathlib import Path as $ALIAS` 뒤 `$ALIAS(..., $PATH).open(...)`로 흐르는 import 별칭 형태도 `pattern-inside`로 결합해 다룬다. 변수에 `Path` 객체를 먼저 담은 뒤 그 변수로 `.open()`을 호출하는 변수 분리 형태는 `pattern-inside`로 같은 변수의 `$VAR = Path(..., $PATH)` 대입과 `$VAR.open(...)` 호출을 결합해 다루며, 관련 없는 변수의 `.open()`(예: `conn.open()`), 여러 `Path` 후보 중 신뢰된 변수 호출, taint 대입 뒤 신뢰된 경로로 재대입한 변수 호출은 탐지하지 않는다. 이 `pattern-inside` 결합은 분기 없이 한 지역 변수에 대입한 뒤 그대로 사용하는 단일 직선 형태만 인식하며, `if`/`else`처럼 조건부 분기 안에서 대입한 뒤 분기 밖의 공유 `.open()` 호출로 이어지는 형태는 실제로 탐지하지 않는다. 이는 문법 형태 인식이며 분기·타입·프레임워크 흐름 해석이 아니다. `os.open`, `shutil`, `Path.read_text`/`read_bytes`/`write_text`/`write_bytes`는 이번 라운드에서도 제외한다. 기존 `secscan.python.open-user-path`(bare `open()`)와는 다른 호출자·sink이므로 별도 규칙 ID를 사용한다.
- JavaScript `Function` 생성자 코드 삽입 규칙은 함수 매개변수가 `Function(..., $CODE)` 또는 `new Function(..., $CODE)`의 마지막 인자(함수 본문)로 흐르는 경우를 하나의 규칙 ID 안에서 `pattern-either`와 `focus-metavariable: $CODE`로 다룬다. 인자 하나인 호출과 `Function("arg", $CODE)`·`new Function("arg", $CODE)`처럼 앞선 인자가 매개변수 이름으로 쓰이는 다중 인자 호출을 모두 포함하지만, `focus-metavariable`이 마지막 인자만 taint 판정 대상으로 제한하므로 매개변수 이름 인자만 tainted이고 본문이 고정값인 호출은 탐지하지 않는다. 기존 `secscan.javascript.eval`(`eval()`)과는 다른 실행 API이므로 별도 규칙 ID를 사용한다.
- JavaScript `insertAdjacentHTML` XSS 규칙은 함수 매개변수가 `$ELEMENT.insertAdjacentHTML($POSITION, $DATA)`의 두 번째 HTML 인자(`$DATA`)로 흐르는 경우만 다룬다. 일반 JavaScript 템플릿 문자열 보간을 포함한다. 위치 인자(`$POSITION`)가 사용자 입력이고 HTML이 고정값인 경우는 `focus-metavariable: $DATA`로 제외한다. `innerHTML`, JSX, React·프레임워크 템플릿·SSR source는 포함하지 않는다. 속성명만으로 sink를 판정하며, 실제 DOM 객체 타입은 해석하지 않는다.
- Java `ProcessBuilder` 운영체제 명령어 삽입 규칙은 접근 제어자(public, protected, private, package-private)와 static 여부에 관계없이 메서드의 `String` 매개변수가 `new ProcessBuilder($COMMAND).start()`로 흐르는 경우를 다룬다. 같은 지역 변수에 생성자를 대입한 뒤 그 변수로 `.start()`를 호출하는 변수 분리 형태(`ProcessBuilder builder = new ProcessBuilder(command); builder.start();`)도 `pattern-inside`로 같은 변수의 선언·대입과 `.start()` 호출을 결합해 다루며, 관련 없는 변수의 `.start()`(예: `worker.start()`), 여러 `ProcessBuilder` 후보 중 신뢰된 변수 호출, taint 대입 뒤 신뢰된 명령으로 재대입한 변수 호출은 탐지하지 않는다. 이 `pattern-inside` 결합도 분기 없이 한 지역 변수에 선언·대입한 뒤 그대로 사용하는 단일 직선 형태만 인식하며, `if`/`else`처럼 조건부 분기 안에서 대입한 뒤 분기 밖의 공유 `.start()` 호출로 이어지는 형태는 실제로 탐지하지 않는다. 이는 문법 형태 인식이며 분기·타입·프레임워크 흐름 해석이 아니다. 다중 인자 생성자(`new ProcessBuilder("sh", "-c", command)`)와 `Runtime.exec`은 이번 라운드에도 포함하지 않는다. 기존 `secscan.java.runtime-exec`과는 다른 프로세스 생성 API이므로 별도 규칙 ID를 사용한다.
- Python `subprocess.run` 운영체제 명령어 삽입 규칙은 동기·비동기 함수 매개변수가 `subprocess.run($COMMAND, shell=True)`로 흐르는 경우를 다룬다. `import subprocess as sp`(별칭)와 `from subprocess import run`(from-import) 결합, 추가 고정 kwargs(`capture_output=True` 등), `shell_flag = True` 같은 지역 상수 `True` 전파를 포함한다. `shell=False`, 상수로 접히지 않는 동적 shell 값, `subprocess.Popen`, `subprocess.call`, `subprocess.check_call`, `subprocess.check_output`, `os.popen`은 포함하지 않는다. 기존 `secscan.python.os-system`과는 다른 API와 `shell=True` 제약이므로 별도 규칙 ID를 사용한다.
- `secscan.javascript.dom-innerhtml` 규칙은 고정 Semgrep OSS 1.95.0에서 `$ELEMENT.innerHTML = $DATA` 패턴이 `innerHTML +=` 복합 대입도 같은 규칙 ID로 탐지하는 실제 동작을 확인했다. `+=` 전용 규칙 ID·KISA 매핑은 추가하지 않으며, 회귀 fixture로 이 동작을 검증한다.

ADR-042 A단계 2차 확장(신규 규칙): 이번 라운드부터 신규 JavaScript 규칙의 source는 ADR-042의 결정에 따라 `function`·`async function` 매개변수만 다루며, 기존 `secscan.javascript.dom-innerhtml`·`secscan.javascript.dom-insert-adjacent-html`이 포함했던 화살표 함수·클래스 메서드·객체 메서드 변형은 신규 규칙에 추가하지 않는다.

- `secscan.javascript.dom-outerhtml` 규칙은 함수·async 함수 매개변수가 `$ELEMENT.outerHTML = $DATA`로 흐르는 경우를 다룬다. 고정 Semgrep OSS 1.95.0에서 이 패턴이 `outerHTML +=` 복합 대입도 같은 규칙 ID로 탐지하는 실제 동작을 확인했으며, 회귀 fixture로 검증한다. `innerHTML`과는 다른 DOM 속성이므로 별도 규칙 ID를 사용한다.
- `secscan.javascript.document-write` 규칙은 함수·async 함수 매개변수가 `document.write($DATA)` 또는 `document.writeln($DATA)`로 흐르는 경우를 하나의 규칙 ID 안에서 `pattern-either`로 다룬다. 두 API는 개행 여부만 다른 같은 문서 스트림 쓰기이므로 근접 쌍 예외로 묶었다. `innerHTML`·`outerHTML`·`insertAdjacentHTML`과는 다른 sink이므로 별도 규칙 ID를 사용한다.
- `secscan.python.pickle-unpickler-load` 규칙은 동기·비동기 함수 매개변수가 `pickle.Unpickler($DATA).load()`로 흐르는 경우를 다룬다. 기존 `secscan.python.pickle-load`(`pickle.load(...)`)·`secscan.python.pickle-loads`(`pickle.loads(...)`)와는 다른 클래스·메서드 호출 sink이므로 별도 규칙 ID를 사용한다.
- `secscan.python.subprocess-popen-shell`, `secscan.python.subprocess-call-shell`, `secscan.python.subprocess-check-call-shell`, `secscan.python.subprocess-check-output-shell` 규칙은 각각 동기·비동기 함수 매개변수가 `subprocess.Popen(shell=True)`, `subprocess.call(shell=True)`, `subprocess.check_call(shell=True)`, `subprocess.check_output(shell=True)`로 흐르는 경우만 다룬다. 서로 다른 메서드 이름이므로 독립 규칙 ID를 사용하며, 기존 `secscan.python.subprocess-run-shell`(`subprocess.run`)과도 다른 API다. `shell=False`, 상수로 접히지 않는 동적 shell 값(예: 매개변수로 받은 `shell_choice`), 대상이 아닌 다른 subprocess API 호출은 탐지하지 않는다. 이번 신규 규칙은 기존 `subprocess-run-shell`과 달리 import 별칭(`import subprocess as sp`)·`from-import` 결합 형태는 sink 패턴에 포함하지 않았으므로, 이런 형태는 알려진 미탐 범위로 남는다.
- `secscan.python.os-popen` 규칙은 동기·비동기 함수 매개변수가 `os.popen($COMMAND)`로 흐르는 경우를 다룬다. 고정 명령 문자열은 탐지하지 않으며, 기존 `secscan.python.os-system`(`os.system(...)`)과는 다른 API이므로 별도 규칙 ID를 사용한다.
- `secscan.python.subprocess-output-shell` 규칙은 동기·비동기 함수 매개변수가 `subprocess.getoutput($COMMAND)` 또는 `subprocess.getstatusoutput($COMMAND)`로 흐르는 경우를 하나의 규칙 ID 안에서 `pattern-either`로 다룬다. 두 API는 반환 형식만 다른 같은 암묵적 셸 실행 계열이므로 근접 쌍 예외로 묶었다. 고정 명령 문자열은 탐지하지 않는다.

ADR-043 B단계 프레임워크 요청 source 확장: 기존 Python 15개 규칙과 Java 3개 규칙의 source를 함수·메서드 매개변수에서 프레임워크 직접 요청 접근으로 확장했다.
- Python 규칙은 `from flask import request`, `from flask import request as $REQ`, `import flask`의 세 가지 import anchor 문맥에서 `request.args`, `request.form`, `request.values`, `request.headers`, `request.cookies`, `request.json`, `request.get_json(...)`, `request.data`, `request.get_data(...)`의 9가지 직접 접근 형태를 source로 다룬다. import anchor가 없는 동명의 로컬 `request`나 `flask` 객체는 오탐 방지를 위해 source로 보지 않는다. Flask view 함수의 URL 경로 매개변수는 기존 함수 매개변수 source가 이미 다루므로 별도 framework source로 중복 추가하지 않는다.
- Java 규칙(`secscan.java.runtime-exec`, `secscan.java.jdbc-statement-sql`, `secscan.java.process-builder`)은 메서드 매개변수 선언이 `HttpServletRequest`, `javax.servlet.http.HttpServletRequest`, `jakarta.servlet.http.HttpServletRequest` 중 하나인 선언 anchor 문맥에서 `$REQ.getParameter(...)`, `$REQ.getHeader(...)`, `$REQ.getPathInfo()`의 세 가지 직접 접근 형태를 source로 다룬다. 실제 classpath나 import를 해석하는 것이 아니라 작성된 매개변수 선언의 구문 형태(syntactic anchor)만 판정하며, Servlet 선언 anchor가 없는 동명 메서드 호출은 source로 보지 않는다. `getPathInfo()`는 서블릿 매핑 뒤 남은 전체 raw path 문자열을 의미하며 Spring `@PathVariable` 등 개별 어노테이션 바인딩을 의미하지 않는다.
- 전파와 한계: Flask와 Java 모두 같은 함수 또는 메서드 안의 일반 지역 변수 대입·재대입 전파를 포함한다. 그러나 사용자 정의 helper 함수, 다른 함수·메서드로의 인자 전달, Spring DI 어노테이션, JSON body 역직렬화 파싱, Servlet cookie 배열 반복과 같은 복합 흐름, sanitizer 및 허용 목록 인식은 포함하지 않는다.
- JavaScript 유지와 후속 공백: JavaScript 규칙에는 anchor 없는 `req.*` source를 추가하지 않고 기존 parameter source 형태를 유지한다. 익명 함수나 화살표 함수 형태의 Express 핸들러는 `dom-innerhtml`을 제외한 대부분의 JavaScript 규칙에서 탐지되지 않는 알려진 후속 공백이며, 이는 함수 source 형태 확장을 위한 별도 ADR·spike로 검토한다.

이 규칙들은 각 언어와 API의 제한된 source-to-sink 형태만 다루며, 모든 프레임워크나 변형을
포괄한다고 주장하지 않는다.
