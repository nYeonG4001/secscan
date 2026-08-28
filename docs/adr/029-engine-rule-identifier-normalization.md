# ADR-029: 엔진 규칙 식별자와 KISA 식별자 분리

**Context**: DAR-006은 진단 결과에 진단 항목 식별자와 명칭을 각각 저장하도록 요구한다. E1의 `FINDING.rule_name`은 명칭 스냅샷용이지만, Semgrep의 `check_id` 같은 엔진 규칙 식별자를 저장할 필드가 없다. 특히 KISA에 매핑되지 않은 결과는 `kisa_code`가 비어 있으므로, 엔진 식별자를 보존하지 않으면 어떤 규칙이 탐지했는지 추적할 수 없다.

**Decision**: `FINDING`에 `engine_rule_id` 문자열 필드를 추가하고 `NOT NULL`로 강제한다. Semgrep 파서는 `check_id`를 변형 없이 `engine_rule_id`에 저장한다. `rule_name`은 사람이 읽는 진단 항목 명칭 스냅샷으로 유지한다. KISA에 매핑된 결과는 카탈로그 `name`을, 미매핑 결과는 엔진이 제공하는 표시명을 우선 저장하고 표시명이 없으면 `engine_rule_id`를 안전한 대체값으로 사용한다.

KISA 매핑은 `FINDING.engine_rule_id`와 `KISA_RULE_MAPPING.engine_rule_id`를 분석 엔진 값과 함께 비교해 찾는다. `kisa_code`는 매핑 성공 때만 저장하고, `criterion_id`와 `recommendation`은 같은 시점의 카탈로그 값으로 복사한다. `engine_rule_id`는 엔진 중립적인 Finding 필드이고, `KISA_RULE_MAPPING`은 엔진별 규칙과 KISA 항목을 연결하는 매핑 데이터다.

`engine_rule_id`는 진단 근거를 식별하는 결과 필드이므로 `FindingUserOut`과 `FindingAdminOut`에 모두 포함한다. 반면 `raw_result`, 실행 로그, 분석 엔진 설정과 오류 상세는 기존 ADR-009에 따라 관리자 전용으로 유지한다.

**Alternatives**: `rule_name`에 Semgrep `check_id`를 저장, `rule_id`라는 Semgrep 전용 Finding 컬럼 추가, 엔진 식별자와 KISA 식별자를 분리해 저장

**Consequences**: E5는 `engine_rule_id`용 Alembic migration, ORM 모델, Pydantic 응답 스키마와 계약 테스트를 추가해야 한다. KISA 매핑 여부는 계속 `kisa_code` 존재 여부로만 계산한다. 실제 rule ID별 KISA 매핑 목록은 E4의 고정 CLI·규칙 출력 확인 뒤 E5-03에서 확정한다.

**References**: ADR-003, ADR-005, ADR-023, DAR-006, DAR-008, SFR-009, SFR-014, QLT-004
