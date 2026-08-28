# ADR-024: 분석 스냅샷과 업로드 상호 배제

**Context**: 분석은 실행 시점의 소스를 보존해야 하며, E3 업로드는 현재 `PROJECT.source_location`을 교체한다. 업로드와 분석 생성이 동시에 시작되면 분석이 이전 소스를 읽거나, 스냅샷 복사 중 현재 소스가 교체될 수 있다.

**Decision**: 분석 요청은 E3의 프로젝트별 업로드 잠금을 짧게 획득해 진행 중 업로드가 없음을 확인한 뒤, 현재 `source_location`, `target_languages`, `analyses/{analysis_id}/source` 스냅샷 위치를 새 `PENDING` 분석 행에 저장하고 commit한다. 업로드 잠금이 있으면 분석 요청은 `409 SOURCE_UPLOAD_IN_PROGRESS`로 거부한다. 이후 `PENDING` 상태가 E3의 새 업로드를 차단한다.

실행기가 `RUNNING`으로 전환한 뒤 현재 소스 전체를 분석별 스냅샷 위치로 복사한다. Semgrep에는 Java `.java`, JavaScript `.js`·`.jsx`·`.mjs`·`.cjs`, Python `.py` 정규 파일만 전달하고, `node_modules`, `vendor`, `dist`, `build`, `target`, `.venv`, `venv`, `__pycache__` 같은 의존성·생성 결과 디렉터리는 제외한다. 전체 스냅샷은 재현성을 위해 보존하며, TypeScript와 설정·문서 파일은 Semgrep 분석 대상이 아니다.

**Alternatives**: 업로드 시 스냅샷 생성, 분석 요청 안에서 동기 복사, 전체 스냅샷을 그대로 Semgrep에 전달, PENDING 저장 후 백그라운드 복사와 대상 파일 필터링

**Consequences**: 분석 요청은 대용량 복사를 기다리지 않고 응답한다. 소스 등록과 분석 생성이 서로 교차하지 않으며, E3의 이전 소스 유예 정리와도 충돌하지 않는다. 서버 재시작으로 분석이 실패하면 미리 기록된 스냅샷 경로가 비어 있거나 일부만 채워질 수 있으며, 해당 분석은 재개하지 않고 새 분석 행으로 재실행한다.

**References**: ADR-017, ADR-019, ADR-021, ADR-022, SFR-007, SFR-008, SFR-011, DAR-005, DAR-008, SEC-007, SEC-008
