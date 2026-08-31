# ADR-005: 진단 결과에 분석 시점 스냅샷 저장

**Context**: FINDING이 KISA_CATALOG을 FK로 참조만 하면 카탈로그의 항목명, 기준 식별자, 심각도를 나중에 수정할 때 과거 분석 결과가 소급 변경된다. 과거 결과의 추적성과 재현성을 해친다.

**Decision**: FINDING에 분석 시점의 항목명(`rule_name`), 기준 식별자(`criterion_id`), 신뢰도(`confidence`), 언어(`language`)를 스냅샷으로 복사 저장한다. KISA_CATALOG은 참조용 마스터 데이터로만 유지한다. KISA에 매핑되지 않은 결과의 `criterion_id`는 비워 둔다.

**Alternatives**: FK 참조만 유지(기각: 카탈로그 수정 시 과거 결과가 바뀌는 문제), 카탈로그 자체를 별도 버전으로 관리

**Consequences**: 정규화 원칙을 일부 어기지만 결과의 감사 추적성 확보 / 저장 공간 소폭 증가(무시 가능한 수준)
