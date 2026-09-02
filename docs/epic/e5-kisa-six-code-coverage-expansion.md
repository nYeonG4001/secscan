# E5 기존 6개 KISA 항목의 직접 API 커버리지 확장 계획

## 목적

현재 SecScan은 자체 Semgrep 규칙 아홉 개를 통해 KISA-001, KISA-002, KISA-003, KISA-004, KISA-005, KISA-043 여섯 항목을 `부분 지원`한다. 이 계획은 새 KISA 코드를 추가하거나 지원 상태를 높이지 않고, 같은 여섯 코드 안에서 아직 다루지 않는 직접 API를 독립 규칙으로 검증하는 실행 순서를 정의한다. 범위 결정은 ADR-041을 따른다.

이 문서는 구현 계획이다. 여기에 적은 예정 규칙, KISA 연결, fixture 기대값은 실제 Semgrep 실행과 CI 증거가 생기기 전까지 카탈로그 상태나 요구사항 충족을 뜻하지 않는다. 2026-09-02 원본 요구사항 문서를 대조한 결과, SFR-010~014, TST-004~006, QLT-002~004는 확장 가능한 다언어 진단·KISA 49개 카탈로그·독립 항목 시험·공통 결과 모델을 요구한다. 원문은 특정 KISA 코드·API 변형·규칙 수를 정하지 않으므로, 후보별 KISA 연결은 기존 카탈로그와 ADR-011·ADR-039·ADR-040의 검증된 분류를 따른다.

## 기준선과 불변 조건

| 항목 | 현재 기준선 | 이번 계획의 처리 |
|---|---|---|
| 엔진 | Semgrep OSS 1.95.0, SecScan 자체 규칙 | 유지. 공식·제3자 규칙을 도입하지 않는다. |
| KISA 범위 | KISA-001/002/003/004/005/043 여섯 코드 | 같은 여섯 코드만 확장한다. 새 코드는 추가하지 않는다. |
| 구현 상태 | 검증된 제한 범위의 `부분 지원` | 유지. `지원`으로 승격하지 않는다. |
| source 모델 | 함수·메서드 매개변수 | 유지. 프레임워크 request source·sanitizer 모델링은 추가하지 않는다. |
| 규칙 식별자 | source-to-sink 계약별 독립 `engine_rule_id` | 새 API를 기존 rule에 합치지 않는다. 같은 API의 `Function(...)`·`new Function(...)` 문법만 한 규칙 안의 `pattern-either`로 묶는다. |

## 완료된 spike와 중단 조건

`innerHTML +=` 사전 spike는 2026-09-02에 production 파일 변경 없이 완료했다. 전용 후보 규칙은 취약 1건·정상 0건을 냈지만, 기존 `secscan.javascript.dom-innerhtml` 규칙도 동일한 `+=` fixture를 한 건 탐지했다. 두 규칙을 같이 실행하면 두 건이므로, 새 `+=` 규칙은 만들지 않는다. 이 결과는 기존 `$ELEMENT.innerHTML = $DATA` 패턴이 고정 Semgrep OSS 1.95.0에서 복합 대입도 매치한다는 뜻이다. 따라서 이 항목은 새 rule ID·매핑·상태 변경 없이 기존 규칙의 회귀 fixture와 provenance에만 반영한다.

다음 항목은 spike 대상도 아니며 이번 라운드에서 제외한다.

- Java `Statement.execute(String)`: Semgrep OSS의 타입 해석 부재로 `Statement`와 `PreparedStatement`를 구별할 수 없다.
- 프레임워크 request source와 framework별 sanitizer: 현재의 함수 매개변수 source 모델과 다른 규칙 종류다.
- `subprocess.Popen`, `call`, `check_call`, `check_output`, `os.popen`, 셸 문자열 조합: `subprocess.run(..., shell=True)`와 합치지 않는다.
- Java 역직렬화, ORM/JPA, `Path.open` 외 파일 API, JavaScript JSX·템플릿·SSR·간접 호출: 별도 범위 결정이 필요하다.
- `Path.open`의 변수 분리, 다중 인자 생성, `.resolve()`·`.joinpath()`, `pathlib.Path(...)` 완전 수식 호출과 import 별칭: 이번 단일 인자 `Path($PATH).open(...)` 규칙에서 제외한다.

## 2026-09-02 전체 사전 검증 결과

모든 spike는 `/tmp`에서 고정 Semgrep OSS 1.95.0과 `--no-rewrite-rule-ids`로 실행했으며, 저장소 파일·매핑·카탈로그 상태는 바꾸지 않았다. 아래 `통과`는 구현 완료가 아니라, 선택한 source-to-sink 계약이 실제 엔진에서 재현됐다는 뜻이다.

| 항목 | 사전 검증 결론 | 구현 시 고정할 범위 |
|---|---|---|
| 기존 `innerHTML` | `+=`는 기존 `secscan.javascript.dom-innerhtml`가 이미 탐지 | 새 규칙·매핑 없음; 기존 규칙에 `+=` 취약·정상 회귀 fixture와 provenance 추가 |
| `secscan.python.path-open` | 통과, 기존 bare `open()` 규칙과 중복 없음 | 단일 인자 `Path($PATH).open(...)`만; 변수 분리·다중 인자·완전 수식·별칭 제외 |
| `secscan.python.pickle-load` | 통과 | 직접 file-like 객체, `io.BytesIO` 래핑, 사용자 경로 → `open()` → `pickle.load()` 전파 포함; 마지막 형태는 KISA-003 Finding과 함께 발생 가능 |
| `secscan.javascript.function-constructor` | 통과, 두 AST 형태가 비중복 | 한 인자 `Function($CODE)`·`new Function($CODE)`을 한 ID의 `pattern-either`로 포함; 다중 인자 제외 |
| `secscan.javascript.dom-insert-adjacent-html` | 통과 | 두 번째 HTML 인자와 템플릿 문자열 보간 포함; 사용자 위치 + 고정 HTML 제외 |
| `secscan.java.process-builder` | 통과, 기존 규칙과 중복 없음 | 모든 접근 제어자·static 여부의 직접 단일 인자 생성자 + 즉시 `start()`; 다중 인자·변수 분리 제외 |
| `secscan.python.subprocess-run-shell` | 통과 | `run`만, `shell=True` 및 지역 상수 `True` 전파·import 별칭·from-import·추가 고정 kwargs 포함; 동적 shell·다른 subprocess API 제외 |

사전 검증을 모두 끝낸 뒤 구현한다. 통과한 신규 규칙 여섯 개와 기존 `innerHTML +=` 회귀 fixture·provenance 보강은 **하나의 보안 구현 PR**에 함께 넣는다. 작업은 규칙별로 독립 구현·검증할 수 있지만, 최종 PR에는 규칙 YAML, 매핑, provenance, fixture, 정규화 테스트와 전체 Ubuntu CI 증거를 모두 포함한다. 각 규칙의 대상 `check_id`·정상 fixture 게이트는 통합 PR 안에서도 독립적으로 유지한다.

기존 카탈로그 분류, Semgrep 표현력, 기대 fixture 중 하나라도 이 계획의 source-to-sink 계약을 지지하지 않으면 해당 후보를 제외하고 사용자에게 범위 재결정을 요청한다. 기대값을 낮추거나 `부분 지원` 상태를 먼저 바꾸지 않는다.

## 규칙 단위 실행 순서

한 규칙이 전환 게이트를 통과하기 전에는 다음 규칙의 카탈로그 매핑을 추가하지 않는다. 구현 PR의 구성은 프로젝트의 현행 보안 변경 절차를 따르되, 각 규칙의 검증과 provenance는 독립적으로 판정 가능해야 한다.

| 순서 | 예정 규칙 ID | KISA 코드 | 구현할 직접 sink | 기존 규칙과의 분리 이유 |
|---|---|---|---|---|
| 1 | `secscan.python.pickle-load` | KISA-043 | `pickle.load($DATA)`와 `io.BytesIO`·`open()` 재대입을 통한 실제 taint 전파 | `pickle.loads($DATA)`와 입력 형태와 sink가 다르다. |
| 2 | `secscan.python.path-open` | KISA-003 | 단일 인자 `Path($PATH).open(...)` | bare `open($PATH, ...)`와 호출자·sink가 다르다. |
| 3 | `secscan.javascript.function-constructor` | KISA-002 | 한 인자 `Function($CODE)` 또는 `new Function($CODE)` | 기존 JavaScript `eval($CODE)`과 실행 API가 다르다. |
| 4 | `secscan.javascript.dom-insert-adjacent-html` | KISA-004 | `$ELEMENT.insertAdjacentHTML($POSITION, $DATA)`의 HTML 인자와 템플릿 문자열 보간 | 직접 `innerHTML = $DATA` 대입과 sink 문법이 다르다. |
| 5 | `secscan.java.process-builder` | KISA-005 | 모든 접근 제어자·static 여부의 `new ProcessBuilder($COMMAND).start()` | `Runtime.getRuntime().exec($COMMAND)`와 프로세스 생성 API가 다르다. |
| 6 | `secscan.python.subprocess-run-shell` | KISA-005 | `subprocess.run($COMMAND, shell=True)`와 지역 상수·import 별칭 전파 | `os.system($COMMAND)`과 API와 `shell=True` 제약이 다르다. |

각 규칙마다 다음 순서를 반복한다.

1. ADR-041과 기존 카탈로그 분류를 대조해 KISA 연결과 제외 범위를 확인한다.
2. 독립 `engine_rule_id`와 고정 source-to-sink 문법을 선언한다. 기존 규칙 ID에 새 API sink를 병합하지 않는다. `Function`의 두 AST 문법만 같은 API로서 하나의 ID 안에 `pattern-either`로 둔다.
3. 취약 fixture와 같은 sink의 고정값 정상 fixture를 작성한다. 정상 fixture는 sanitizer·타입 안전성·모든 API 변형의 안전을 주장하지 않는다.
4. 고정 YAML과 `--no-rewrite-rule-ids`로 Semgrep OSS 1.95.0을 직접 실행해 취약 fixture의 **대상 규칙** 접두어 없는 `check_id` 1건과 정상 fixture의 대상 규칙 0건을 확인한다. 같은 파일에 서로 다른 sink가 있으면 각 Finding의 ID·줄·KISA 매핑을 따로 기대한다.
5. 규칙 YAML, `RULES_PROVENANCE.md`, `KISA_RULE_MAPPING_SEED`, fixture, `test_real_semgrep_vulnerable_fixtures_normalize_to_mapped_findings`, `test_real_semgrep_safe_fixtures_do_not_trigger_the_tested_rule`, E5 증거 문서를 같은 변경에서 갱신한다.
6. 정규화된 Finding이 해당 `engine_rule_id`와 기존 KISA 코드로 저장되는지 확인한다. 카탈로그는 여섯 코드 모두 `부분 지원`으로 유지한다.

## 전환 게이트와 검증

규칙별 최소 게이트는 모두 필수다.

1. `engine_rule_id`가 YAML·매핑 시드·fixture 기대값에서 유일하고, 기존 규칙을 덮어쓰지 않는다.
2. 취약 fixture는 실제 Semgrep 실행에서 대상 접두어 없는 `check_id`를 정확히 1건 낸다. 다른 규칙이 다른 sink 줄에서 Finding을 낼 경우 전체 결과 수와 혼동하지 않고, 별도 기대값으로 검증한다.
3. 정상 fixture는 대상 `check_id`를 0건 낸다.
4. 실제 결과가 E5 정규화를 거쳐 같은 KISA 코드·심각도·신뢰도로 저장된다.
5. provenance에 KISA/CWE/OWASP 근거, source, sink, 타입·이름 해석 한계, 제외 범위를 한국어로 기록한다.
6. 관련 집중 테스트, 필터 없는 전체 백엔드 pytest, Ruff, `git diff --check`, GitHub Actions Ubuntu CI가 통과한다.

예상 검증 명령은 구현 시점의 `CONTRIBUTING.md`를 우선하되, 최소한 다음 범위를 포함한다.

```bash
cd backend
pytest -q tests/test_e5_result_normalization.py
pytest -q
ruff check .
git diff --check
```

Semgrep의 직접 실행 명령과 fixture별 기대 `check_id`는 구현 PR에 그대로 기록한다. 로컬 통과만으로 카탈로그 상태·요구사항 매트릭스의 완료 증거를 갱신하지 않으며, GitHub Actions Ubuntu CI가 통과한 뒤에만 사실에 맞게 갱신한다.

## 문서와 리뷰 산출물

| 산출물 | 구현 전 | 규칙별 게이트 통과 뒤 |
|---|---|---|
| ADR-041 | 여섯 후보와 제외 범위의 기준 | spike 통과처럼 결정이 바뀔 때만 갱신 |
| `RULES_PROVENANCE.md` | 변경하지 않음 | 규칙 ID별 근거·sink·제외 범위 추가 |
| E5-10 및 이 계획 | 계획 상태 | 실제 구현·fixture·CI 증거를 사실대로 반영 |
| `docs/requirements-matrix.md` | 변경하지 않음 | 요구사항 증거가 생긴 항목만 링크 추가 |
| 카탈로그 상태 | 여섯 코드 `부분 지원` 유지 | 여섯 코드 `부분 지원` 유지 |

의미 있는 구현 변경은 `AGENTS.md`의 순서에 따라 Codex 구현·검증 뒤 Claude가 요구사항, 보안, 회귀, 테스트를 검토하고, 수용한 지적을 반영한 뒤 다시 검증한다. 이번 계획에는 Claude의 사전 검토 의견을 반영했지만, 실제 규칙 diff의 코드 리뷰를 대체하지 않는다.

## 완료 정의

이번 계획은 문서화 단계에서 완료된다. 구현 단계의 완료는 예정 규칙 수가 아니라, 각 규칙이 독립 전환 게이트와 Ubuntu CI를 통과한 사실로만 판단한다. 어느 후보도 검증 전에는 `지원`으로 표시하지 않으며, 이후 확장에 적용할 KISA 항목 또는 규칙 수 상한도 정하지 않는다.

## 관련 문서

- [ADR-041](../adr/041-six-kisa-direct-api-expansion.md)
- [E5 결과 정규화](e5-result-normalization.md) E5-10
- [E7 SAST 평가와 규칙 확장 계획](e7-sast-evaluation-plan.md)
- [ADR-039](../adr/039-self-authored-rule-coverage-expansion.md)
- [ADR-040](../adr/040-python-rule-extensions-for-existing-kisa-codes.md)
