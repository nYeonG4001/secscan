# ADR-037: 진단 결과 목록 정렬·필터·페이지네이션

**Context**: 완료 분석의 Finding은 수가 많아질 수 있으므로, 사용자가 심각한 결과부터 확인하고 주요 속성으로 좁힐 수 있어야 한다. 클라이언트가 전체 결과를 받은 뒤 필터링하면 목록 크기에 따라 초기 로딩과 메모리 사용량이 커진다. 또한 offset 페이지네이션은 완전한 정렬 기준이 없으면 같은 행이 중복되거나 누락될 수 있다.

**Decision**: `GET /api/findings`가 `severity`, `mapping_status`, `language`, `limit`, `offset`을 서버에서 처리한다. 응답은 `items`, `total`, `limit`, `offset`을 반환한다. 기본 정렬은 `CRITICAL`, `HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`, 상대 `file_path`, 시작 `line`, Finding ID 순이다. `limit` 기본값은 50, 서버 상한은 100이다.

`GET /api/findings`는 목록 전용 경량 응답 스키마를 사용한다. 목록 `items`에는 심각도, 진단 항목명, KISA 코드, 상대 파일·시작/끝 줄, 언어, 신뢰도, KISA 매핑 상태만 포함한다. 엔진 규칙 식별자와 분석 시점 기준 식별자, 메시지, 탐지 근거, 코드 조각, 조치 권고와 원본 결과는 `GET /api/findings/{finding_id}` 상세 응답에서만 제공한다. 텍스트 검색, 기준 코드 검색, 신뢰도 필터는 MVP에서 제공하지 않는다.

**Alternatives**: 클라이언트 전체 조회 뒤 필터링, 텍스트·코드·신뢰도까지 포함한 복합 검색, 정렬 기준 없이 offset만 적용, 커서 페이지네이션

**Consequences**: API와 테스트에 목록 전용 응답 스키마, 목록 응답 envelope, 안정 정렬을 추가해야 한다. 목록 응답에서 상세·관리자 전용 데이터를 제외해 전송량과 노출 범위를 줄인다. MVP에서는 구현과 설명이 간단한 offset 페이지네이션을 사용하며, 결과량이 크게 늘면 이후 커서 페이지네이션으로 교체할 수 있다.

**References**: ADR-028, ADR-031, ADR-032, ADR-035, SFR-016, SFR-017, DAR-006, DAR-008, TST-007
