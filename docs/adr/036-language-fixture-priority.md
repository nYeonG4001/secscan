# ADR-036: 언어별 취약 코드와 정상 코드 fixture 우선순위

**Context**: MVP는 Java, JavaScript, Python을 지원하지만, 고정한 Semgrep 보안 규칙의 실제 언어별 커버리지와 KISA 매핑 가능 수는 E4 구현 뒤에야 확인할 수 있다. 모든 언어와 KISA 49개 항목에 고정된 구현 수를 미리 약속하면 실제 규칙 지원과 맞지 않을 수 있다. 또한 보안 규칙 팩은 하나의 샘플에서 검증 대상과 무관한 Finding을 만들 수 있다.

**Decision**: E4의 고정 CLI와 규칙을 실제 실행해 확인한 규칙부터 Java, JavaScript, Python의 fixture를 만든다. 초기 fixture는 Java 외부 입력→`Runtime.exec`, JavaScript 외부 입력→`eval`, Python 외부 입력→`pickle.loads`의 취약 코드와, 같은 API에 고정·신뢰된 값을 전달하는 정상 코드를 한 쌍씩 둔다. 각 취약 fixture는 해당 규칙 하나의 KISA 매핑 Finding 1건을, 정상 fixture는 검증 대상 규칙의 미탐지를 기대한다. taint 규칙의 `pattern-sources` 표현과 취약 fixture의 외부 입력 표현은 같은 변경에서 함께 검토한다. 이후 언어당 규칙이 늘어나면 정상 코드에서 전체 Finding 수 0건을 요구하지 않고, 계속 검증 대상 규칙의 미탐지만 확인한다. 실제 fixture는 KISA 매핑의 명확성, 다언어 지원 여부, 교육적 설명 가능성, 재현 안정성 순으로 추가한다. 기대 Finding 수는 Semgrep 원시 매치 수가 아니라 정규화와 ADR-035 중복 제거 뒤 저장된 최종 Finding 수다.

Java에서 최소 KISA 매핑 fixture를 만들 수 없으면 기준을 낮추지 않는다. ADR-023에 따라 필요한 자체 규칙을 독자 작성해 추가하고 코드 리뷰 PR에서 KISA/CWE/OWASP 근거와 기대 결과를 검토한다. TypeScript는 확장 구조만 유지하고 MVP fixture 우선순위에서는 제외한다. 고정 탐지 항목 수는 정하지 않고 검증 가능한 항목을 최대한 추가한다.

**Alternatives**: 언어 하나만 우선 지원, 언어별 고정 탐지 수 약속, 정상 코드에서 전체 Finding 0개 요구, Java 최소 기준 완화

**Consequences**: 실제 엔진 지원을 과장하지 않으면서 세 지원 언어의 검증 근거를 만들 수 있다. fixture, 고정 CLI와 규칙 revision, KISA 매핑 데이터는 함께 갱신해야 한다. 정규화 오류가 나면 개수 비교 대신 `ENGINE_OUTPUT_INVALID` 실패를 검증한다. 실제 서비스 규칙이 모두 KISA에 매핑되는 경우에도, 미매핑 결과 보존은 테스트 전용 합성 Semgrep JSON fixture로 별도 검증한다.

**References**: ADR-011, ADR-023, ADR-030, ADR-034, ADR-035, SFR-010, SFR-011, TST-004, TST-005, QLT-002, QLT-003, QLT-004, SEC-010
