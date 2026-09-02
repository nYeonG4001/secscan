# E5 기존 6개 KISA 항목의 B단계 프레임워크 요청 source 확장 계획

## 목적

ADR-041·ADR-042의 A단계는 함수·메서드 parameter에서 직접 API sink로 흐르는 값을 대상으로 했다. 이 계획은 같은 여섯 KISA 코드에서 Flask 전역 요청 객체와 Servlet 요청 객체의 직접 접근값을 기존 rule ID의 추가 source로 검증·구현하기 위한 B단계 계약이다.

원본 요구사항 문서는 특정 framework, rule ID, API 수 또는 KISA 상태를 고정하지 않는다. 따라서 이 계획은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043만 계속 `부분 지원`하고, 새 코드·매핑·`지원` 상태·규칙 수 상한을 만들지 않는다. 요구사항 연결은 SFR-010~014, TST-004~006, QLT-002~004를 따른다.

## 기준선과 불변 조건

| 항목 | 고정 조건 |
|---|---|
| 엔진 | Semgrep OSS 1.95.0과 SecScan 자체 `mode: taint` 규칙만 사용한다. 공식·제3자 규칙은 도입하지 않는다. |
| rule ID·KISA | 새 rule ID·`KISA_RULE_MAPPING_SEED` 행·KISA 코드·카탈로그 상태 변경은 만들지 않는다. 기존 source에만 `pattern-sources` 항목을 추가한다. |
| 적용 언어 | Python 현재 15개 rule ID와 Java 현재 3개 rule ID를 대상으로 한다. JavaScript rule source는 이번 구현에서 변경하지 않는다. |
| 흐름 | 같은 함수·메서드 안의 일반 지역 변수 전파는 포함한다. helper·함수 간 흐름·간접 호출·route/controller 해석·DI·sanitizer 인식은 제외한다. |
| 오탐 방지 | Flask는 import anchor, Java는 Servlet parameter declaration anchor가 없으면 source로 보지 않는다. anchor 없는 동명이인 음성 fixture는 필수다. |
| PR 구성 | ADR-043과 이 계획을 문서 PR 하나로 제출한다. 통과 source 전체의 production YAML·provenance·fixture·정규화 테스트는 이후 구현 PR 하나로 제출한다. |

## 완료된 spike와 범위 결론

모든 spike는 production YAML을 수정하지 않고 `/tmp`의 비-`tests` 경로 fixture로 실행했다. 저장소 fixture를 제자리에서 직접 실행하면 Semgrep 기본 `.semgrepignore`가 `tests/` 경로를 무시할 수 있으므로, 0건 결과는 임시 복사 경로에서만 판단한다.

| 언어·형태 | 결론 | 검증된 범위와 처리 |
|---|---|---|
| Flask `from flask import request` | 통과 | `args`, `form`, JSON, `headers`, `cookies`, `values`, `data`, `get_data()`가 representative Python sink에 각각 1건, 고정값 0건, 지역 전파 1건이다. Flask import 없는 동명 객체는 0건이다. |
| Flask import alias | 통과 | `from flask import request as req`와 source metavariable 결합이 기본 import와 같은 결과를 냈다. 별칭은 제외하지 않고 source 계약에 포함한다. |
| Flask module import | 통과 | `import flask`와 `flask.request` 접근도 같은 결과를 냈다. source 계약에 포함한다. |
| Flask path parameter | 신규 source 아님 | view 함수의 path parameter는 기존 generic function parameter source가 이미 탐지한다. 별도 framework source로 추가하거나 지원 범위를 과장하지 않는다. |
| Servlet query/form·header | 통과 | `getParameter(...)`, `getHeader(...)`는 선언 anchor가 있을 때 representative Java sink에 각 1건, 고정값 0건, 지역 전파 1건이다. |
| Servlet raw path | 통과 | `getPathInfo()`는 raw path 문자열 source로 1건 탐지된다. Spring `@PathVariable` 지원을 뜻하지 않는다. |
| Servlet short/FQN 선언 | 통과 | short `HttpServletRequest`, `javax.servlet.http.HttpServletRequest`, `jakarta.servlet.http.HttpServletRequest` 세 declaration branch를 함께 써야 모두 지원한다. 같은 sink 줄 중복은 없다. |
| Servlet JSON·cookie | 제외 | JSON은 stream reader/input stream 뒤 파싱이 필요하고, cookie는 배열 반복·이름 비교가 필요해 단일 직접 source 계약을 넘는다. |
| Express `req.*` | 구현 변경 없음 | named handler의 `req.query`, `req.params`, `req.body`, header, cookie는 기존 generic parameter source가 이미 전파한다. unanchored `req.*` pattern은 동명 일반 객체를 오탐하므로 추가하지 않는다. |
| 익명·화살표 Express handler | 알려진 후속 공백 | `dom-innerhtml` 외 대부분의 JavaScript rule은 named function source가 중심이다. JS 함수 형태 확장은 framework source와 다른 축이므로 별도 ADR·spike로 검토한다. |

## 구현 전환 대상과 fixture 계약

| 순서 | 처리 | 대상 | 필수 검증 |
|---|---|---|---|
| 1 | 기존 ID source 확장 | Python 15개 rule ID에 Flask direct source | import 기본·alias·module form, accessor별 취약 1건, 고정값 0건, 지역 전파, Flask 없는 동명이인 0건 |
| 2 | 기존 ID source 확장 | Java 3개 rule ID에 Servlet direct source | `getParameter`·`getHeader`·`getPathInfo`, short·`javax` FQN·`jakarta` FQN declaration, 고정값·지역 전파·non-Servlet 유사 객체 음성 검증 |
| 3 | 회귀·중복 검증 | 모든 수정 rule ID | generic parameter와 framework source의 같은 sink 줄 1건, production config 같은 sink 줄 다중 rule 0건, 기존 취약·정상 fixture 전체 재실행 |

각 accepted source accessor·anchor는 직접 source→sink fixture, 고정/신뢰 값 fixture, 지역 전파 fixture, anchor가 없는 동명이인 객체 fixture를 가진다. source accessor가 같은 언어 모든 rule에 반복 적용되는 경우에도, 각 수정 rule ID는 최소 하나 이상의 framework source→기존 sink fixture로 실제 적용을 검증한다.

기존 fixture는 fixture 이름이 `safe`여도 다른 새 rule에 실제 취약 sink가 있을 수 있으므로, 전체 Finding 수가 아니라 검증 대상 `check_id`와 sink 줄을 기준으로 기대값을 기록한다. `safe_subprocess_run_popen.py`의 기존 target-rule 전용 음성 계약처럼, 문서화된 교차 Finding은 숨기지 않고 별도 기대값으로 다룬다.

## 구현과 검증 순서

1. 구현 PR에서 기존 rule ID의 `pattern-sources`에만 accepted anchor·accessor를 추가한다. existing parameter source와 sink pattern, KISA mapping, status seed를 변경하지 않는다.
2. Semgrep OSS 1.95.0과 `--no-rewrite-rule-ids`로 fixture를 비-`tests` 임시 경로에 복사해 직접 실행한다. 각 target `check_id`의 취약 1건, 고정/anchor 음성 0건, 지역 전파, 같은 sink 줄 중복 0건을 확인한다.
3. 각 수정 rule ID의 기존 취약·정상 fixture 전체와 새 fixture를 production config로 재실행한다. source OR 확장 때문에 기존 fixture가 예상 밖에 넓어지지 않는지 확인한다.
4. `RULES_PROVENANCE.md`에는 Flask import form, Java three-branch declaration, raw path의 의미, anchor·type 이름 기반 한계, JS anonymous handler 후속 공백을 기록한다. `test_e5_result_normalization.py`에는 실제 Semgrep 취약·정상 기대값과 anchor 회귀 fixture를 추가한다.
5. 집중 E5 테스트, 필터 없는 `pytest -q`, `ruff check .`, `git diff --check`, GitHub Actions Ubuntu CI를 통과해야 한다. macOS RLIMIT_AS 제한은 기존 troubleshooting 기록을 따르며 product resource policy를 바꾸지 않는다.

후보가 어느 gate라도 명확히 통과하지 못하면 구현 PR에서 제외하고, ADR-043과 이 계획에 실제 근거를 기록한다. 기대값을 낮추거나 KISA 상태를 먼저 바꾸지 않는다.

## 완료 정의와 이후 단계

이 문서 PR의 완료는 ADR-043과 spike 결론·source 문법·제외 범위·전환 게이트를 검토 가능하게 기록하는 것이다. 이후 구현 PR의 완료는 모든 대상 source가 아니라, 실제 구현한 각 source/rule 조합이 fixture·정규화·Ubuntu CI 증거를 통과한 사실로 판단한다.

후속 검토 대상은 JavaScript 익명·화살표 handler source 형태, Spring DI body/path binding, Servlet JSON parsing·cookie 반복, sanitizer/allowlist 인식, framework wrapper·함수 간 흐름이다. 이들은 이번 source accessor 확장과 다른 오탐·해석 정책을 가지므로 별도 spike·ADR로만 다룬다.

## 관련 문서

- [ADR-043](../adr/043-framework-request-source-expansion.md)
- [ADR-042](../adr/042-kisa-direct-api-phase-a-round-2.md)
- [ADR-041](../adr/041-six-kisa-direct-api-expansion.md)
- [E5 결과 정규화](e5-result-normalization.md) E5-10
