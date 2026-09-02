# ADR-043: 기존 6개 KISA 항목의 프레임워크 요청 source 확장

**Context**: PR #54가 ADR-042의 직접 API A단계 2차 확장을 구현·Ubuntu CI 검증까지 마쳤다. 현재 SecScan은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043을 자체 Semgrep `mode: taint` 규칙 24개로 제한적으로 `부분 지원`한다. 기존 규칙의 source는 함수·비동기 함수·Java 메서드의 매개변수이며, 이 모델은 함수 인자로 직접 전달된 입력은 다루지만 Flask 전역 `request`와 `HttpServletRequest`에서 읽은 값은 정확한 source 정의 없이는 일관되게 다루지 못한다.

원본 요구사항 DOCX는 `docs/development-workflow.md` 8절에 따라 저장소 밖의 기준 문서로 보관한다. ADR-041이 2026-09-02에 기록한 대조 결과처럼 SFR-010~014, TST-004~006, QLT-002~004는 Java·JavaScript·Python의 확장 가능한 진단, KISA 49개 카탈로그, 항목별 독립 검증, 공통 결과 모델을 요구하지만 특정 framework API·규칙 수·`지원` 상태를 고정하지 않는다. 따라서 이번 결정은 이미 `부분 지원`인 여섯 KISA 코드에서 검증 가능한 source 형태만 넓히며, 새 KISA 코드·engine rule ID·매핑·상태 승격을 만들지 않는다.

사전 spike는 production YAML을 수정하지 않고 `/tmp`의 비-`tests` 경로에서 고정 Semgrep OSS 1.95.0과 `--no-rewrite-rule-ids`로 수행했다. Flask와 Servlet의 이름 충돌 오탐을 확인한 뒤 import·선언 문맥 anchor를 추가했으며, 취약 흐름 1건, 고정값 0건, 지역 변수 전파, 기존 parameter source와의 같은 sink 줄 중복 0건을 재현했다.

**Decision**: 기존 함수·메서드 parameter source는 유지하고, 아래 source만 기존 같은 언어의 rule ID에 추가한다. source 확장은 sink·KISA 매핑·severity·confidence 계약을 바꾸지 않는다. 모든 결과는 계속 기존 rule ID와 여섯 기존 KISA 코드로 정규화하며, 카탈로그 상태는 `부분 지원`으로 유지한다.

| 언어 | 추가 source와 anchor | 적용 범위 | 포함 HTTP 입력 |
|---|---|---|---|
| Python | `from flask import request`, `from flask import request as $ALIAS`, `import flask` 문맥에 각각 결합한 Flask `request` 접근 | 현재 Python rule ID 전체 | `args`, `form`, JSON(`json`, `get_json()`), `headers`, `cookies`, query/form 통합 `values`, raw body(`data`, `get_data()`) |
| Java | 메서드 매개변수 선언이 짧은 `HttpServletRequest`, `javax.servlet.http.HttpServletRequest`, `jakarta.servlet.http.HttpServletRequest` 중 하나인 문맥 | 현재 Java rule ID 전체 | `getParameter(...)`의 query/form, `getHeader(...)`, raw path 문자열 `getPathInfo()` |
| JavaScript | 추가 없음 | 기존 JavaScript rule ID 유지 | Express `req`가 현재 parameter source 형태로 이미 흐르는 범위만 기존 동작으로 유지 |

- Flask source는 라우트 데코레이터를 해석하지 않는다. 위 import anchor와 직접 접근 형태가 있으면 위치와 무관하게 source로 본다. Flask view 함수의 path parameter는 이미 기존 함수 parameter source가 다루므로 새 framework source로 주장하지 않는다.
- Flask의 세 import 형태는 동등한 지원 범위다. alias·module import를 임의로 제외하지 않으며, anchor 없이 `request` 또는 `flask`라는 이름만 보는 pattern은 사용하지 않는다. 이는 이름만 같은 로컬 객체의 확인된 오탐을 막기 위한 조건이다.
- Java source는 실제 classpath·import 해석이 아니라 작성된 매개변수 선언의 세 문법 형태를 결합한 syntactic anchor다. short-name `HttpServletRequest`와 두 inline FQN branch를 모두 둬야 `javax`·`jakarta` inline 선언을 놓치지 않는다. `getPathInfo()`는 개별 Spring `@PathVariable`이 아니라 servlet mapping 뒤 남은 전체 raw path 문자열이다.
- Flask·Java 모두 같은 함수 또는 메서드 안의 일반 지역 변수 대입·재대입 전파는 고정 엔진의 실제 taint 동작으로 포함한다. 사용자 정의 helper, 다른 함수·메서드로의 전달, framework DI, route/controller/decorator 구조 해석, 간접 호출, sanitizer·허용 목록 인식은 포함하지 않는다.
- JavaScript에는 `req.query`, `req.params`, `req.body`, header, cookie를 위한 unanchored `req.*` source를 추가하지 않는다. 새 pattern은 이름만 `req`인 일반 객체를 오탐했고, plain JavaScript에는 Flask import나 Java type처럼 비용 없이 신뢰할 anchor가 없다. 또한 Express 요청값의 기존 parameter-source 탐지는 source 형태에 따라 다르다. `secscan.javascript.dom-innerhtml`만 익명 함수·화살표 함수·클래스/객체 메서드까지 넓은 source를 갖고, `secscan.javascript.eval`, `secscan.javascript.function-constructor`, `secscan.javascript.dom-insert-adjacent-html`, `secscan.javascript.dom-outerhtml`, `secscan.javascript.document-write`는 이름 있는 함수 형태가 중심이다. 따라서 익명·화살표 Express handler의 후자 rule들 미탐은 이번 결정의 알려진 공백이며, JS 함수 source 형태 확장은 별도 ADR·spike로만 검토한다.

다음은 이번 source 확장에서 제외한다.

- Java JSON body의 `getInputStream()`·`getReader()` 뒤 파싱, Servlet cookie array 반복과 `Cookie.getName()` 비교, Spring `@RequestBody`·`@PathVariable` 등 DI binding
- Flask/JavaScript의 사용자 정의 wrapper, framework serializer·validator·sanitizer·허용 목록의 안전성 판정
- Java 실제 타입·import 해석, ORM/JPA, React·JSX·SSR, 간접 호출
- ADR-041·ADR-042가 sink 쪽에서 이미 제외한 `Statement.execute(String)`·`addBatch(String)`, `Runtime.exec`의 추가/변수 분리 sink 형태, 문자열 `setTimeout`·`setInterval`, Path read/write 계열, Java 역직렬화

각 source form은 구현 PR에 들어가기 전에 다음 전환 게이트를 모두 만족해야 한다.

1. 각 accepted accessor·anchor에는 직접 source→sink 취약 fixture, 고정/신뢰 값 fixture, 같은 함수·메서드의 지역 전파 fixture가 있다. 각 확장 대상 rule ID에는 최소 하나 이상의 framework source→기존 sink fixture가 있어야 한다.
2. Flask에는 Flask import가 없는 동명 `request`/`flask` 객체, Java에는 Servlet 선언 anchor가 없는 `getParameter` 유사 객체의 음성 fixture를 추가해 대상 rule ID가 0건인지 확인한다. 이는 anchor 제거·약화의 회귀를 막는 필수 계약이다.
3. 기존 generic parameter source와 새 framework source가 같은 sink 줄에서 만나도 대상 `check_id`가 한 건이며, production config 전체에서 같은 sink 줄의 다중 rule 결과가 0건인지 확인한다.
4. 각 수정 rule ID의 기존 취약·정상 fixture 전부와 새 fixture를 비-`tests` 임시 경로에 복사해 Semgrep OSS 1.95.0, `--no-rewrite-rule-ids`로 다시 실행한다. 기존 fixture에 새 source가 우연히 넓게 적용되지 않는지 확인한다.
5. `RULES_PROVENANCE.md`, 실제 Semgrep 정규화 fixture·테스트, 집중 E5 테스트, 필터 없는 `pytest -q`, `ruff check .`, `git diff --check`, GitHub Actions Ubuntu CI를 같은 구현 PR에서 검증한다. macOS의 기존 RLIMIT_AS Semgrep sandbox 제한은 `docs/troubleshooting/2026-09-01-e5-local-semgrep-sandbox-validation.md`을 따르며 제품 제한을 완화하지 않는다.

**Consequences**: 구현은 새 source pattern을 기존 Python 15개와 Java 3개 rule ID에 추가하지만, 새 mapping 행·migration·API·카탈로그 상태 변경은 만들지 않는다. source 정의가 넓어져 기존 sink의 탐지 결과 수는 늘 수 있으므로, 구현 PR은 source accessor별 fixture와 모든 수정 rule의 기존 fixture 재실행 증거를 함께 보존한다. Flask import 및 Servlet declaration anchor는 source 계약의 일부이므로 `RULES_PROVENANCE.md`에 지원 문법과 이름·타입 기반 한계를 기록한다.

이 결정은 JS anonymous/arrow handler source 확장, sanitizer 인식, framework DI와 multi-step body/cookie 해석을 미룬다. 이 후속 범위는 source·오탐 정책이 달라지므로 이번 구현 PR에 섞지 않고 별도 spike·ADR로 검토한다.

**Alternatives**: 기존 parameter source만 유지, Flask·Servlet을 anchor 없이 이름 패턴으로 추가, Express `req.*` source를 unanchored pattern으로 추가, 모든 framework·DI·sanitizer를 같은 라운드에 포함, framework별 새 rule ID·KISA mapping 생성, 공식 또는 제3자 Semgrep 규칙 도입

**References**: ADR-011, ADR-023, ADR-030, ADR-039, ADR-040, ADR-041, ADR-042, `docs/epic/e5-result-normalization.md` E5-10, `docs/epic/e5-framework-source-expansion.md`, SFR-010, SFR-011, SFR-014, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
