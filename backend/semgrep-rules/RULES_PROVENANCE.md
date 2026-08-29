# SecScan 자체 규칙 출처

이 디렉터리의 규칙은 SecScan이 독자 작성한 규칙이다. Semgrep 공식 규칙이나 다른 제3자
Semgrep 규칙의 패턴·로직을 복사하거나 변형하지 않았다. 규칙 변경은 근거 검토와 예상 결과
테스트 갱신을 포함한 별도 PR로 진행한다.

| 규칙 `id` | 언어 | 공개 보안 근거 | 작성·변경 사유 |
|---|---|---|---|
| `secscan.java.runtime-exec` | Java | CWE-78, OWASP Top 10 2021 A03 | 운영체제 명령 주입 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.javascript.eval` | JavaScript | CWE-95, OWASP Top 10 2021 A03 | 문자열 코드 실행 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.python.pickle-loads` | Python | CWE-502, OWASP Top 10 2021 A08 | 신뢰할 수 없는 역직렬화 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |

E5는 `secscan-security.yml` 파일을 `--config`로 직접 지정하고
`--no-rewrite-rule-ids`를 함께 사용한다. Semgrep OSS 1.95.0 실제 출력에서 위 `id`와 같은
접두어 없는 `check_id`를 확인했으며, 이를 고정 `engine_rule_id`와 매핑 시드에 사용한다.

- Java 규칙은 메서드의 `String` 매개변수가 `Runtime.getRuntime().exec(...)`로 흐르는 경우를 다룬다.
- JavaScript 규칙은 함수 매개변수가 `eval(...)`로 흐르는 경우를 다룬다.
- Python 규칙은 함수 매개변수가 `pickle.loads(...)`로 흐르는 경우를 다룬다.

이 규칙들은 각 언어와 API의 제한된 source-to-sink 형태만 다루며, 모든 프레임워크나 변형을
포괄한다고 주장하지 않는다.
