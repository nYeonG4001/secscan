# ADR-032: 진단 결과 심각도와 신뢰도 정규화

**Context**: KISA 카탈로그는 항목별 기본 심각도를 제공하지만 신뢰도는 제공하지 않는다. Semgrep 같은 분석 엔진은 자체 심각도와 선택적인 신뢰도 메타데이터를 제공할 수 있으며, 표기와 누락 여부가 규칙마다 다를 수 있다. 원문 값을 그대로 저장하면 결과 필터와 화면 표시가 일관되지 않고, 카탈로그 기본 심각도의 오타도 매핑 결과 전체에 전파될 수 있다.

**Decision**: KISA 매핑 Finding의 `severity`는 정규화 시점의 `KisaCatalog.default_severity`를 복사한다. 미매핑 Finding은 엔진 심각도를 다음 공통 값으로 정규화한다: `CRITICAL`은 `CRITICAL`, `HIGH` 또는 `ERROR`는 `HIGH`, `MEDIUM` 또는 `WARNING`은 `MEDIUM`, `LOW` 또는 `INFO`는 `LOW`, 누락되었거나 알 수 없는 값은 `UNKNOWN`이다. `confidence`는 KISA 매핑과 무관하게 엔진 메타데이터만 `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`으로 정규화하며, 심각도에서 추론하지 않는다.

`FINDING.severity`는 `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`만 허용하고, `FINDING.confidence`는 `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`만 허용하는 DB 체크 제약을 둔다. `KISA_CATALOG.default_severity`는 관리자가 정하는 기준값이므로 `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`만 허용하고 `UNKNOWN`은 허용하지 않는다.

Semgrep OSS 1.95.0과 초기 자체 규칙의 실제 출력은 `extra.severity: ERROR`을 제공하고 신뢰도 메타데이터는 제공하지 않는다. 따라서 초기 매핑 Finding은 KISA 카탈로그의 `HIGH`를 심각도로 복사하고, 신뢰도는 `UNKNOWN`으로 저장한다. 이후 규칙이 신뢰도 메타데이터를 제공하면 이 ADR의 공통 정규화 규칙을 적용한다.

**Alternatives**: 엔진 원문 등급 저장, 모든 결과에 엔진 심각도만 사용, 심각도에서 신뢰도 추론, 등급 문자열을 제약 없이 저장

**Consequences**: 매핑 결과는 KISA 기준의 일관된 위험도를 보이고, 미매핑 결과도 의미를 잃지 않고 정렬과 필터링할 수 있다. 과거 Finding은 분석 시점 등급을 보존하므로 카탈로그 기본 심각도가 변경되어도 바뀌지 않는다. E5 migration은 세 체크 제약과 정규화 테스트를 추가해야 한다.

**References**: ADR-005, ADR-011, ADR-023, ADR-031, DAR-006, DAR-007, DAR-008, SFR-014, SFR-017, QLT-004
