# ADR-039: 자체 Semgrep 규칙 커버리지 확장

**Context**: SecScan은 KISA 49개 항목을 모두 카탈로그로 제공하지만, 실제 탐지는 검증된 자체 Semgrep 규칙 범위로만 표시한다. 초기 규칙은 Java 운영체제 명령어 삽입, JavaScript 코드 삽입, Python 신뢰할 수 없는 데이터의 역직렬화 세 항목만 `부분 지원`으로 연결한다. 공식 또는 제3자 Semgrep 규칙은 Public 저장소와 다중 사용자 서비스에 맞지 않는 라이선스 조건 때문에 사용하지 않는다. 발표 전 실제 탐지 범위를 늘리되, 한 규칙이 KISA 항목 전체를 포괄하는 것처럼 표시해서는 안 된다.

**Decision**: 기존 세 규칙과 같은 자체 작성 `mode: taint` 방식으로 아래 세 규칙을 추가한다. 구현과 직접 Semgrep 실행, KISA 매핑, 취약·정상 fixture 검증이 모두 끝난 뒤에만 해당 카탈로그 상태를 `부분 지원`으로 바꾼다. `지원` 상태는 이번 확장에서도 사용하지 않는다.

| 규칙 ID | KISA 항목 | 언어 | source → sink 범위 | 공개 근거 |
|---|---|---|---|---|
| `secscan.java.jdbc-statement-sql` | KISA-001 SQL 삽입 | Java | 메서드 `String` 매개변수 → `executeQuery(String)` 또는 `executeUpdate(String)` | CWE-89, OWASP A03:2021 |
| `secscan.javascript.dom-innerhtml` | KISA-004 크로스사이트 스크립트 | JavaScript | 함수 매개변수 → `$ELEMENT.innerHTML = $DATA` 직접 대입 | CWE-79, OWASP A03:2021 |
| `secscan.python.open-user-path` | KISA-003 경로 조작 및 자원 삽입 | Python | 함수 매개변수 → 내장 `open($PATH, ...)` | CWE-22, OWASP A01:2021 |

- Java 규칙은 `execute(String)`, `executeUpdate(String, int)`, `PreparedStatement`, ORM, JPA를 포함하지 않는다. 메서드명만으로 sink를 판정하므로 실제 JDBC 타입 해석은 하지 않는다.
- JavaScript 규칙은 `$ELEMENT.innerHTML = $DATA` 패턴을 사용한다. 고정 Semgrep OSS 1.95.0의 2026-09-02 직접 검증에서 이 패턴은 `innerHTML +=`도 같은 `secscan.javascript.dom-innerhtml` 규칙으로 탐지했다. 따라서 `+=` 전용 규칙 ID·KISA 매핑은 추가하지 않는다. React·템플릿·SSR·`insertAdjacentHTML`과 프레임워크별 sanitizer는 포함하지 않는다. 속성명만으로 sink를 판정하므로 실제 DOM 객체 타입은 해석하지 않는다.
- Python 규칙은 bare builtin `open()`만 포함한다. `Path.open`, `os.open`, `shutil`, 압축 해제와 업로드 경로 검증은 포함하지 않는다. 로컬에서 `open` 이름을 재정의한 코드는 이번 범위에서 구분하지 않는다.
- Java와 Python의 정상 fixture는 각각 PreparedStatement 바인딩과 고정 서버 관리 경로를 사용한다. 이는 모든 sanitizer·경로 검증 전략의 안전성을 판정한다는 뜻이 아니라, 이 규칙의 source-to-sink 형태가 없을 때 미탐지되는지를 확인하는 범위다.
- 모든 신규 취약 fixture는 고정 YAML 파일과 `--no-rewrite-rule-ids`로 실제 Semgrep OSS를 직접 실행해, 정확히 한 건의 접두어 없는 `check_id`가 나오는지 확인한다. 확인한 값만 `KISA_RULE_MAPPING` 시드에 사용한다.
- 카탈로그 구현 상태는 초기 `부분 지원` 3개에서 검증 뒤 6개가 된다. 이는 향후 고정 탐지 항목 수 약속이 아니라, 해당 revision의 검증된 실제 범위다.

**Alternatives**: 초기 세 규칙만 유지, 세 항목을 `지원`으로 표시, `execute(String)`·여러 프레임워크·다른 파일 API까지 한 번에 포함, 공식 또는 제3자 Semgrep 규칙 사용

**Consequences**: 언어별 실제 탐지 예제가 두 개씩 생겨 시연과 회귀 검증 범위가 넓어진다. 반면 모든 규칙은 제한된 문법적 source-to-sink 형태만 다루므로 `RULES_PROVENANCE.md`에 sink 한계와 근거를 함께 기록해야 한다. 규칙 YAML, 매핑 시드, 카탈로그 상태, fixture와 기대 결과 테스트는 하나의 보안 관련 구현 PR에서 함께 변경하고 코드 리뷰를 생략하지 않는다. 스키마·마이그레이션·새 API는 추가하지 않는다.

**References**: ADR-011, ADR-023, ADR-030, ADR-036, SFR-010, SFR-011, TST-004, TST-005, QLT-002, QLT-003, SEC-010
