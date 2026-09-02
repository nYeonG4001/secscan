# E5 기존 6개 KISA 항목의 직접 API A단계 2차 확장 계획

## 목적

PR #52와 ADR-041이 구현한 직접 API 확장 뒤에도, 같은 여섯 KISA 코드에는 함수·메서드 매개변수 source만으로 재현 가능한 인접 sink가 남아 있다. 이 계획은 ADR-042의 후보를 실제 규칙으로 구현하기 전 필요한 spike 결과, fixture 경계, 문서화와 통합 PR 게이트를 정의한다.

원본 요구사항 문서는 특정 KISA 코드·API·규칙 수를 고정하지 않는다. 따라서 이 계획은 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043의 `부분 지원` 범위만 넓히며, 새 코드·`지원` 상태·규칙 수 상한을 만들지 않는다. 요구사항 연결은 SFR-010~014, TST-004~006, QLT-002~004를 따른다.

## 기준선과 불변 조건

| 항목 | 고정 조건 |
|---|---|
| 엔진 | Semgrep OSS 1.95.0과 SecScan 자체 `mode: taint` 규칙만 사용한다. 공식·제3자 규칙을 도입하지 않는다. |
| KISA 범위와 상태 | 기존 여섯 코드만 `부분 지원`으로 유지한다. 후보 개수나 구현 규칙 수의 상한을 정하지 않는다. |
| source | 함수·비동기 함수·Java 메서드 매개변수만 source다. request 객체와 sanitizer·허용 목록 모델은 B단계의 별도 ADR 대상이다. |
| 규칙 ID | 다른 함수·메서드 이름은 독립 ID가 기본이다. `write/writeln`, `getoutput/getstatusoutput`, 기존 JDBC SQL 실행 계열처럼 동일 sink 의미가 검증된 근접 쌍만 예외적으로 한 ID에 묶는다. |
| 실제 dataflow | 고정 엔진의 별칭·상수·wrapper·재대입 전파는 실제 탐지 범위로 문서화한다. 선언한 제외와 다르게 엔진이 흐름을 잡으면 기대값을 숨기지 않는다. |
| PR 구성 | ADR-042와 이 계획은 문서 PR 하나에 넣는다. 이후 통과 후보 전체의 YAML·매핑·provenance·fixture·정규화 테스트는 구현 PR 하나에 넣는다. |

## 완료된 사전 spike와 제외

모든 spike는 production YAML을 수정하지 않고 `/tmp`의 비-`tests` 경로 fixture에서 `--no-rewrite-rule-ids`로 고정 Semgrep OSS 1.95.0을 실행했다. Semgrep 기본 `.semgrepignore`가 `tests/` 형태의 경로를 무시하므로, 저장소 fixture를 제자리에서 직접 실행한 0건 결과는 규칙 실패 근거로 사용하지 않는다.

| 항목 | 결론 | 이유와 처리 |
|---|---|---|
| `outerHTML =`·`+=` | 통과 | tainted RHS 1건, 고정값 정상 0건. `innerHTML`과 다른 속성이므로 신규 ID 후보로 유지한다. |
| `document.write`·`document.writeln` | 통과 | 각 취약 형태가 탐지되고 고정값 정상은 0건. newline만 다른 같은 문서 스트림 쓰기로 한 ID에 묶는다. |
| `pickle.Unpickler(file).load()` | 통과 | 취약 1건·정상 0건이며 `pickle.load`와 다른 클래스 메서드 sink로 신규 ID 후보로 유지한다. |
| `Popen`·`call`·`check_call`·`check_output`의 `shell=True` | 통과 | 각 API의 취약 형태와 정상·`shell=False` 제외를 재현했다. 서로 다른 메서드 이름이므로 독립 ID를 쓴다. |
| `os.popen`, `getoutput`, `getstatusoutput` | 통과 | 암묵적 셸 실행 형태가 취약 1건·정상 0건이다. 후자의 두 API만 한 ID에 묶는다. |
| 다중 인자 Function 생성자 | 통과 | 마지막 함수 본문 인자가 tainted이면 탐지하고, 매개변수 이름만 tainted인 정상 fixture는 탐지하지 않는다. 기존 ID를 확장한다. |
| `executeLargeUpdate(String)` | 통과 | 기존 JDBC String-SQL 실행 계열과 같은 직접 sink로 기존 ID의 `pattern-either` 확장 후보로 유지한다. |
| `Path.open` 표현식 변형 | 통과 | 완전 수식·import 별칭·다중 인자·`joinpath`·`resolve`를 기존 ID 확장 후보로 유지한다. |
| `Path.open` 변수 분리 | 통과 | `pattern-inside`가 같은 `Path` 변수와 `.open()`을 결합하고 관련 없는 `.open()`·재대입은 제외한다. 표현식 변형과 별도의 fixture 묶음으로 구현한다. |
| `ProcessBuilder` 변수 분리 | 통과 | `pattern-inside`가 같은 builder와 `.start()`를 결합하며 관련 없는 `.start()`·재대입은 제외한다. 기존 ID 확장 후보로 유지한다. |
| 문자열 `setTimeout`·`setInterval` | 제외 | parameter가 string인지 callback인지 타입을 구분하지 못해 정상 callback 전달을 탐지한다. |
| `Statement.addBatch(String)` | 제외 | 호출 시점에는 SQL을 실행하지 않고 큐에 넣는다. |
| `Statement.execute(String)` | 제외 유지 | Java 실제 타입을 해석하지 못해 `Statement`와 `PreparedStatement`를 안전하게 구별할 수 없다. |
| `Runtime.exec` 추가 문법 | 신규 후보 아님 | 기존 규칙의 음성 회귀 fixture로만 확인한다. |
| Path read/write 계열 | 이번 라운드 제외 | 별도 파일 I/O API의 KISA·source-to-sink 범위를 이번 spike에서 확정하지 않았다. |

## 구현 전환 대상과 fixture 계약

| 순서 | 처리 | 대상 | 필수 취약·정상·제외 검증 |
|---|---|---|---|
| 1 | 신규 ID | `outerHTML`, `document.write/writeln`, `pickle.Unpickler.load` | tainted sink 1건, 고정값 0건, 기존 `innerHTML`·`pickle.load`와 같은 줄 중복 0건 |
| 2 | 신규 ID | explicit·implicit Python 셸 API | API별 tainted 명령 1건, 고정 명령 0건, `shell=False`·동적 shell·비대상 API 0건, import 별칭·from-import·지역 상수의 실제 동작 기록 |
| 3 | 기존 ID 확장 | Function 마지막 본문 인자, JDBC `executeLargeUpdate` | 마지막 body taint 1건·tainted parameter-name 0건, 기존 JDBC SQL fixture와 expected ID·KISA 일치 |
| 4 | 기존 ID 확장 | `Path.open` 표현식 변형 | 완전 수식·별칭·다중 인자·체인마다 대상 ID 1건, 고정 경로·비대상 파일 API 0건 |
| 5 | 기존 ID 확장 | `Path.open`·`ProcessBuilder` 변수 분리 | 올바른 같은 변수의 흐름 1건, shadowed 변수·관련 없는 receiver·재대입 뒤 신뢰된 객체·여러 객체 후보 0건 |

각 신규 ID는 `KISA_RULE_MAPPING_SEED`의 고유성, `RULES_PROVENANCE.md`의 KISA/CWE/OWASP·source·sink·제외 범위, 취약·정상 fixture, `test_e5_result_normalization.py`의 실제 Semgrep 정규화 기대값을 함께 추가한다. 기존 ID 확장은 새 mapping 행을 만들지 않지만 provenance와 fixture·정규화 테스트를 변경한 범위까지 갱신한다.

`Path.open`처럼 하나의 fixture에서 기존 `open-user-path`와 새/확장 Path sink가 서로 다른 줄에 함께 발생하면, 전체 결과 수가 아니라 규칙 ID·줄·KISA 코드별 별도 Finding을 기대한다. 같은 sink 줄에서 두 규칙이 함께 발생하면 대상 후보는 중복으로 제외하거나 기존 규칙으로 통합한다.

## 구현과 검증 순서

1. 구현 PR에서 production YAML과 실제 fixture를 추가·확장한다. spike 임시 YAML을 그대로 복사하지 않고, 규칙 ID·메시지·metadata·매핑·provenance를 최종 계약과 대조한다.
2. Semgrep OSS 1.95.0과 `--no-rewrite-rule-ids`로 저장소 fixture를 비-`tests` 임시 디렉터리에 복사하여 직접 실행한다. 대상 취약 fixture의 대상 `check_id` 1건, 정상·제외 fixture의 대상 `check_id` 0건, production config와의 같은 줄 중복 0건을 확인한다.
3. `test_real_semgrep_vulnerable_fixtures_normalize_to_mapped_findings`, `test_real_semgrep_safe_fixtures_do_not_trigger_the_tested_rule`와 변수 분리·기존 ID 확장 전용 테스트를 갱신한다. E5 정규화 뒤 engine rule ID, 기존 KISA 코드, `HIGH` 심각도, `UNKNOWN` 신뢰도가 저장되는지 확인한다.
4. 집중 E5 테스트, 필터 없는 `pytest -q`, `ruff check .`, `git diff --check`와 GitHub Actions Ubuntu CI를 통과해야 한다. macOS의 기존 RLIMIT_AS Semgrep sandbox 제한은 `docs/troubleshooting/2026-09-01-e5-local-semgrep-sandbox-validation.md`을 따르며 제품 리소스 정책을 완화하지 않는다.

후보가 이 게이트 중 하나라도 명확히 통과하지 못하면 구현 PR에서 제외하고 ADR·이 계획에 실제 결론을 기록한다. 기대값을 낮추거나 카탈로그 상태를 먼저 바꾸지 않는다.

## 완료 정의와 이후 단계

이 문서 PR의 완료는 ADR-042와 후보별 spike·제외·게이트가 검토 가능하게 기록되는 것이다. A단계 구현 완료는 목록의 모든 후보가 아니라, 구현한 각 후보가 독립 fixture·정규화·Ubuntu CI 증거를 통과한 사실로만 판단한다.

A단계 뒤 Spring `@RequestParam`, `HttpServletRequest`, Express `req.body`, Flask `request.args` 같은 framework source를 B단계로 검토할 수 있다. 이때는 기존 sink를 재사용하더라도 source 정의, sanitizer 정책, 오탐 기준과 사용자 영향이 달라지는 별도 ADR과 spike가 필요하다.

## 관련 문서

- [ADR-042](../adr/042-kisa-direct-api-phase-a-round-2.md)
- [ADR-041](../adr/041-six-kisa-direct-api-expansion.md)
- [1차 직접 API 확장 계획](e5-kisa-six-code-coverage-expansion.md)
- [E5 결과 정규화](e5-result-normalization.md) E5-10
