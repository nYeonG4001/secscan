# ADR-023: 고정 Semgrep 실행과 자체 KISA 규칙

**Context**: E5의 KISA 매핑과 E7의 기대 결과 검증은 Semgrep `rule_id`가 변하지 않는다는 전제에 의존한다. 실행할 규칙이 자동 선택·갱신되면 같은 소스의 결과와 KISA 매핑이 달라질 수 있다.

**Decision**: 고정 버전의 Semgrep OSS CLI와 SecScan 자체 작성 규칙만 실행한다. 고정 YAML 파일을 직접 지정해 YAML `id`와 같은 안정적인 `engine_rule_id`를 사용한다. 공식 `p/security-audit` 규칙은 Rules License v1.0의 재배포·타인 대상 서비스 제공 제한 때문에 사용하지 않는다.

자체 규칙은 KISA, CWE, OWASP 공개 기준을 근거로 독자 작성하고, 출처·근거·변경 사유는 `RULES_PROVENANCE.md`에 기록한다. 외부 입력이 위험 API까지 도달한 경우만 탐지하며, 알려진 모든 변형을 포괄하지 않으므로 구현 상태는 `부분 지원`으로 표시한다. 규칙 변경은 KISA 매핑 검토와 기대 결과 테스트 갱신을 포함한 별도 PR로 관리한다.

**Alternatives**: `--config auto`, 원격 언어별 규칙 팩 직접 지정, 공식 규칙 팩의 저장소 고정본, Semgrep의 별도 재배포 허가 요청

**Consequences**: 같은 이미지와 규칙 고정본에서는 같은 `rule_id`와 KISA 매핑을 기대할 수 있다. 초기 탐지 범위는 작을 수 있으므로 KISA 49개 카탈로그와 실제 탐지 지원 항목을 분리해 표시하고, 검증 가능한 자체 규칙을 계속 추가한다.

**References**: SFR-008, SFR-010, SFR-011, TST-005, QLT-003, SEC-010
