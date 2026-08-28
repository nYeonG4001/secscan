# SecScan 자체 규칙 출처

이 디렉터리의 규칙은 SecScan이 독자 작성한 규칙이다. Semgrep 공식 규칙이나 다른 제3자
Semgrep 규칙의 패턴·로직을 복사하거나 변형하지 않았다. 규칙 변경은 근거 검토와 예상 결과
테스트 갱신을 포함한 별도 PR로 진행한다.

| Semgrep 출력 ID / 규칙 `id` | 언어 | 공개 보안 근거 | 작성·변경 사유 |
|---|---|---|---|
| `semgrep-rules.secscan.java.runtime-exec` / `secscan.java.runtime-exec` | Java | CWE-78, OWASP Top 10 2021 A03 | 운영체제 명령 주입 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `semgrep-rules.secscan.javascript.eval` / `secscan.javascript.eval` | JavaScript | CWE-95, OWASP Top 10 2021 A03 | 문자열 코드 실행 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |
| `semgrep-rules.secscan.python.pickle-loads` / `secscan.python.pickle-loads` | Python | CWE-502, OWASP Top 10 2021 A08 | 신뢰할 수 없는 역직렬화 위험 API의 직접 사용을 탐지하기 위해 최초 작성 |

Semgrep는 디렉터리 구성 파일로 실행할 때 출력 `check_id`에 디렉터리 이름을 붙인다. 위의
출력 ID는 Semgrep OSS CLI 1.95.0에서 검증한 실제 식별자이고, 뒤의 `id`는 이 저장소의
규칙 파일에 기록한 SecScan 규칙 식별자다.
