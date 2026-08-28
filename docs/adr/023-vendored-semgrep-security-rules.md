# ADR-023: 고정된 Semgrep 보안 규칙 팩

**Context**: E5는 Semgrep 결과의 `rule_id`를 `KISA_RULE_MAPPING.engine_rule_id`와 연결해 KISA 항목을 판정한다. 실행 시 Semgrep 레지스트리가 규칙을 자동 선택하거나 갱신하면, 같은 소스가 다른 `rule_id`를 내거나 기존 매핑이 미매핑 결과로 바뀔 수 있다. 이는 기대 결과를 검증하는 E7 테스트와 분석 시점 재현성에 맞지 않는다.

**Decision**: 고정 버전의 Semgrep OSS CLI를 백엔드 이미지에 포함하고, 공식 `p/security-audit` 규칙 팩의 허용된 고정본을 `backend/semgrep-rules/` 아래에서 실행한다. 실행은 `--json --quiet --oss-only`를 사용한다. 규칙 파일을 가져올 때 출처, 버전 또는 revision, 라이선스, 가져온 날짜를 `backend/semgrep-rules/THIRD_PARTY_NOTICES.md`에 기록한다.

규칙 파일과 Semgrep CLI 버전 변경은 SEC-010의 외부 구성요소 갱신 대상으로 관리한다. 변경은 별도 PR, 라이선스 재확인, 영향을 받는 KISA 매핑과 기대 결과 테스트 갱신을 함께 요구한다. Java 커버리지는 E5에서 실제 매핑 개수와 샘플 결과를 확인한 뒤 필요한 공식 규칙만 추가한다.

**Alternatives**: `--config auto`, 원격 언어별 규칙 팩 직접 지정, 공식 규칙 팩의 저장소 고정본, 자체 규칙 대량 작성

**Consequences**: 분석 실행은 런타임 규칙 레지스트리에 의존하지 않고, 같은 소스와 같은 이미지·규칙 고정본에서 같은 `rule_id`를 기대할 수 있다. 보안 중심 규칙을 우선해 일반 스타일·정확성 규칙의 미매핑 결과를 줄인다. Java에서 E5의 최소 매핑 검증을 충족하지 못하면 조건을 낮추지 않고 필요한 공식 규칙 추가를 별도 라이선스 확인과 코드 리뷰 PR로 검토한다. 규칙 파일은 탐지 범위를 바꾸는 보안 코드로 취급하므로 코드 리뷰를 생략하지 않는다.

**References**: SFR-008, SFR-010, SFR-011, TST-005, QLT-003, SEC-010
