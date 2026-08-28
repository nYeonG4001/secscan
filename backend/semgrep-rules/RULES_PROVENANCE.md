# SecScan 자체 규칙 출처

이 디렉터리의 규칙은 SecScan이 독자 작성한 규칙이다. Semgrep 공식 규칙이나 다른 제3자
Semgrep 규칙의 패턴·로직을 복사하거나 변형하지 않았다. 규칙 변경은 근거 검토와 예상 결과
테스트 갱신을 포함한 별도 PR로 진행한다.

| 규칙 `id` | 언어 | 공개 보안 근거 | 작성·변경 사유 |
|---|---|---|---|
| `secscan.java.runtime-exec` | Java | CWE-78, OWASP Top 10 2021 A03 | 운영체제 명령 주입 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.javascript.eval` | JavaScript | CWE-95, OWASP Top 10 2021 A03 | 문자열 코드 실행 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `secscan.python.pickle-loads` | Python | CWE-502, OWASP Top 10 2021 A08 | 신뢰할 수 없는 역직렬화 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |

E4의 디렉터리 직접 지정 실행은 실행 경로에 따라 `check_id` 앞에 접두어를 붙이는 것을
확인했다. E5 구현에서는 각 YAML 파일을 `--config`로 직접 지정해, 위의 `id` 값을 접두어
없는 고정 `check_id`와 `engine_rule_id`로 사용한다. 매핑 시드와 fixture는 이 전환 뒤 실제
출력을 다시 확인해 갱신한다.
