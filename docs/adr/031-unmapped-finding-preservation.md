# ADR-031: 미매핑 진단 결과 보존과 엔진 규칙 식별자 노출

**Context**: 외부 분석 엔진의 모든 결과가 KISA 49개 항목에 즉시 연결되지는 않는다. 결과를 버리면 탐지 범위를 설명하거나 후속 매핑을 추가할 근거가 사라진다. 반대로 KISA 카탈로그에 자동 추가하면 관리 기준과 실제 탐지 결과가 섞이고, 임의 매핑이 생길 수 있다. 또한 `engine_rule_id`는 개별 탐지 규칙을 식별하지만 실행 로그나 분석 엔진 설정과 같은 운영 정보는 아니다.

**Decision**: 정규화에 성공한 결과는 KISA 매핑 여부와 관계없이 Finding으로 저장한다. 미매핑 결과는 `kisa_code`, `criterion_id`, `recommendation`을 비워 두고, `engine_rule_id`, `rule_name`, 심각도, 신뢰도, 언어, 상대 파일 위치, 메시지, 탐지 근거, `raw_result`를 보존한다. KISA 카탈로그 항목 또는 구현 상태를 자동으로 만들거나 변경하지 않는다. 매핑 추가는 ADR-030의 버전 관리 데이터와 코드 리뷰 절차로만 수행한다.

권한 있는 USER와 ADMIN은 매핑과 미매핑 결과를 모두 조회하고 `engine_rule_id`를 확인할 수 있다. `raw_result`, 실행 로그, 오류 상세, 분석 엔진 설정은 ADR-009에 따라 ADMIN 전용으로 유지한다.

**Alternatives**: 미매핑 결과 폐기, 미매핑 전용 테이블 분리, 미매핑 결과의 KISA 카탈로그 자동 생성, `engine_rule_id`를 관리자 전용으로 제한

**Consequences**: 결과 수와 KISA 매핑 수를 구분해 설명할 수 있고, 이후 규칙 매핑을 추가해도 과거 미매핑 결과의 탐지 근거를 잃지 않는다. 결과 API와 UI는 `UNMAPPED` 상태를 지원해야 하며, USER 응답에는 원본 결과를 넣지 않는다.

**References**: ADR-009, ADR-011, ADR-029, ADR-030, SFR-009, SFR-014, DAR-006, DAR-008, SEC-003, SEC-009, QLT-004
