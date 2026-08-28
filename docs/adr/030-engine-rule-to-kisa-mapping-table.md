# ADR-030: 엔진 규칙과 KISA 항목의 다대일 매핑

**Context**: 하나의 KISA 항목은 언어별 또는 패턴별 여러 Semgrep 규칙으로 탐지될 수 있다. 기존 `KISA_CATALOG.semgrep_rule_id` 단일 컬럼은 KISA 항목 하나에 규칙 하나만 연결할 수 있고, 같은 Semgrep 규칙이 여러 KISA 항목에 잘못 연결되는 것을 막는 제약도 제공하지 않는다.

**Decision**: `KISA_RULE_MAPPING` 테이블을 추가한다. 이 테이블은 `id`, `engine`, `engine_rule_id`, `kisa_code`를 저장하고, `UNIQUE(engine, engine_rule_id)`와 `KISA_CATALOG.kisa_code` 외래키를 가진다. 여러 매핑 행이 하나의 KISA 항목을 참조할 수 있지만, 하나의 엔진 규칙은 최대 하나의 KISA 항목에만 연결된다.

기존 `KISA_CATALOG.semgrep_rule_id`는 E5 migration에서 제거한다. 현재 이 필드를 노출하는 `CatalogItemOut`에서 제거하며, 생성·수정 스키마에는 매핑 필드를 추가하지 않는다. 카탈로그 API는 매핑 필드를 제공하지 않는다. 매핑은 관리자 UI나 공개 API로 임의 변경하지 않고, 고정 Semgrep 규칙과 함께 코드 리뷰 PR의 시드 또는 버전 관리 데이터로 갱신한다. E5-03은 고정 YAML 파일을 직접 지정한 실제 출력 `check_id`만 시드에 사용한다.

초기 매핑 시드는 `semgrep` 엔진의 `secscan.java.runtime-exec → KISA-005`(운영체제 명령어 삽입), `secscan.javascript.eval → KISA-002`(코드 삽입), `secscan.python.pickle-loads → KISA-043`(신뢰할 수 없는 데이터의 역직렬화)다. 세 항목은 현재 한정된 source-to-sink 패턴만 탐지하므로 카탈로그 구현 상태를 `부분 지원`으로 설정한다.

**Alternatives**: KISA 카탈로그의 단일 `semgrep_rule_id` 유지, 다대다 허용 매핑 테이블, 엔진 규칙 하나를 하나의 KISA 항목에만 연결하는 다대일 매핑 테이블

**Consequences**: Java, JavaScript, Python의 여러 규칙을 같은 KISA 항목으로 연결할 수 있고, 매핑 조회가 항상 결정적이다. E5는 새 ORM 모델, Alembic migration, 시드와 매핑 무결성 테스트를 추가해야 한다. 매핑은 관리 API 범위가 아니므로 별도 `/api/rule-mappings` 엔드포인트를 만들지 않는다.

**References**: ADR-003, ADR-023, ADR-029, SFR-010, SFR-012, SFR-013, SFR-014, QLT-002, QLT-003, SEC-003, SEC-010
