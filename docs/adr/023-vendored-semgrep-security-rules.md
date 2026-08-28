# ADR-023: 고정 Semgrep 실행과 자체 KISA 규칙

**Context**: E5는 Semgrep 결과의 `rule_id`를 `KISA_RULE_MAPPING.engine_rule_id`와 연결해 KISA 항목을 판정한다. 실행 시 Semgrep 레지스트리가 규칙을 자동 선택하거나 갱신하면, 같은 소스가 다른 `rule_id`를 내거나 기존 매핑이 미매핑 결과로 바뀔 수 있다. 이는 기대 결과를 검증하는 E7 테스트와 분석 시점 재현성에 맞지 않는다.

**Decision**: 고정 버전의 Semgrep OSS CLI를 백엔드 이미지에 포함하고, `backend/semgrep-rules/` 아래의 SecScan 자체 작성 규칙만 실행한다. 실행은 `--json --quiet --oss-only`를 사용한다. 규칙 디렉터리를 `--config`로 넘기지 않고, 고정 YAML 파일을 각각 직접 지정한다. 이렇게 하면 실행 위치가 `check_id` 앞에 붙지 않아 YAML의 `id` 값을 안정적인 `engine_rule_id`로 사용한다. 규칙은 KISA 가이드, CWE, OWASP 같은 공개 기준을 근거로 독자 작성하며, Semgrep 공식 규칙 또는 다른 제3자 규칙의 패턴·로직을 복사하거나 변형하지 않는다. 각 자체 규칙의 규칙 ID, KISA/CWE/OWASP 근거, 지원 언어, 작성·변경 사유는 `backend/semgrep-rules/RULES_PROVENANCE.md`에 기록한다.

Semgrep CLI 버전은 SEC-010의 외부 구성요소 갱신 대상으로 관리하고, 출처와 라이선스는 `backend/THIRD_PARTY_NOTICES.md`에 기록한다. 자체 규칙 변경은 탐지 범위를 바꾸는 보안 코드이므로 별도 PR, KISA 매핑 검토, 영향을 받는 기대 결과 테스트 갱신을 함께 요구한다. E5에서는 외부 입력이 위험 API까지 도달한 경우만 탐지하도록 각 초기 규칙을 `mode: taint`의 source-to-sink 규칙으로 보완한다. 이 규칙들은 알려진 모든 프레임워크·우회 경로를 포괄하지 않으므로, 대응 KISA 항목의 구현 상태는 `부분 지원`으로 표시한다. Java 커버리지가 부족하면 E5에서 실제 샘플 결과를 근거로 필요한 자체 규칙을 독자 작성해 추가한다.

공식 `p/security-audit` 규칙은 Semgrep Rules License v1.0이 규칙의 배포와 타인 대상 서비스 제공을 허용하지 않아, Public 저장소와 다중 사용자 교육용 서비스인 SecScan에 벤더링하거나 런타임 다운로드로 제공하지 않는다.

**Alternatives**: `--config auto`, 원격 언어별 규칙 팩 직접 지정, 공식 규칙 팩의 저장소 고정본, Semgrep의 별도 재배포 허가 요청

**Consequences**: 분석 실행은 런타임 규칙 레지스트리에 의존하지 않고, 같은 소스와 같은 이미지·자체 규칙 고정본에서 같은 `rule_id`를 기대할 수 있다. 초기 탐지 범위는 공식 규칙 팩 전체보다 작을 수 있으므로, 카탈로그 49개와 실제 탐지 지원 항목을 분리해 구현 상태로 표시한다. 지원 항목 수를 미리 고정하지 않고, 검증 가능한 자체 규칙을 추가한다. 규칙 파일은 탐지 범위를 바꾸는 보안 코드로 취급하므로 코드 리뷰를 생략하지 않는다.

**References**: SFR-008, SFR-010, SFR-011, TST-005, QLT-003, SEC-010
