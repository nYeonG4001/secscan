# ADR-035: 분석 실행 내부 Finding 중복 제거 지문

**Context**: 분석 엔진이 같은 규칙과 같은 코드 위치를 중복 보고하면 결과 목록과 요약 수가 부풀려진다. 원본 JSON 전체 비교는 출력의 비본질적 차이에 취약하고, 규칙 ID와 파일 경로만 비교하면 같은 파일의 서로 다른 취약점을 합쳐 버린다. `end_line`은 엔진 중립성을 위해 NULL을 허용하므로, 원시 컬럼의 복합 UNIQUE만으로는 PostgreSQL의 NULL 고유성 동작 때문에 중복을 완전히 막을 수 없다.

**Decision**: Finding마다 내부 `finding_fingerprint` SHA-256 값을 저장하고 `(analysis_id, finding_fingerprint)` UNIQUE 제약을 둔다. 지문 원문은 `engine_rule_id`, 정규화한 상대 `file_path`, `line`, 유효 끝 줄을 순서대로 NUL 문자(`\x00`)로 구분해 UTF-8로 인코딩한다. 유효 끝 줄은 `end_line`이 있으면 그 값, 없으면 `line`, `line`도 없으면 `NO_LINE` 표식이다. `finding_fingerprint`은 API나 화면에 노출하지 않는다.

동일 지문이 같은 분석 실행에서 다시 나오면 엔진 출력 순서상 첫 결과만 저장한다. 분석 실행이 다르면 소스 스냅샷과 실행 시점이 다르므로 중복 제거하지 않는다. E3에서 ZIP 내부 경로의 NUL 문자를 거부하고, 규칙 ID는 고정된 벤더링 규칙에서 오므로 NUL 구분자는 지문 입력 충돌을 만들지 않는다.

**Alternatives**: 원본 JSON 전체 비교, 규칙 ID와 파일 경로만 비교, 원시 컬럼 복합 UNIQUE, 중복 제거하지 않음

**Consequences**: 여러 줄 범위가 없거나 NULL인 엔진 결과도 같은 위치의 중복을 안정적으로 막는다. 서로 다른 필드 조합이 구분자 없는 문자열 연결로 충돌하는 문제를 피한다. E5 migration은 `finding_fingerprint`과 UNIQUE 제약을, 테스트는 NUL 구분자와 NULL 끝 줄 정규화를 검증해야 한다.

**References**: ADR-016, ADR-029, ADR-033, ADR-034, SFR-014, DAR-006, DAR-008, QLT-004
