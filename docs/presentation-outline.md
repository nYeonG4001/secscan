# 발표 뼈대

이 문서는 중간발표(8/31)와 최종발표(9/3)에서 어떤 항목을 어느 문서에서 가져다 쓸지 미리 정리한 포인터 모음이다. 지금 시점의 진행 상태나 시연 내용은 적지 않는다. 발표 직전에 확정할 항목은 `[발표 직전 작성]` 또는 `[구현 완료 후 작성]`으로 표시한다.

## 중간발표 (8/31)

### 이해한 요구사항
→ 참고: `docs/requirements-interpretation.md`

### MVP 범위와 제외 이유
→ 참고: `docs/mvp.md`, `docs/epic/epic-sast-mvp.md`(범위/제외 절)

### 현재 설계·구현 상태
→ 참고: `docs/erd.md`, `docs/adr/001-semgrep.md`, `docs/requirements-matrix.md`(상태 열)

### 주요 설계 결정(ADR) 요약
→ 참고: `docs/adr/`(001~012 전체 목록에서 발표 시점에 부각할 항목 선별)

### 남은 3일(9/1–3) 작업 배치
→ [발표 직전 작성]

## 최종발표 (9/3)

### 문제와 RFP, 내가 이해한 핵심
→ 참고: `docs/requirements-interpretation.md` 요약

### 요구사항과 범위 (항목 번호 대응)
→ 참고: `docs/requirements-matrix.md`

### 아키텍처와 기술 선택
→ 참고: `docs/implementation-strategy.md`, `docs/adr/002-tech-stack.md`, `docs/erd.md`

### 보안 설계와 자체 적용 사례
→ 참고: `docs/sast-self-application.md`, `docs/adr/008-unauthorized-response-policy.md`, `docs/adr/009-role-based-response-schema.md`, `docs/adr/012-external-component-security.md`

### 동작 시연
→ [구현 완료 후 작성]

### 테스트와 검증 증거
→ 참고: `docs/requirements-matrix.md`(테스트/증거 열), `docs/troubleshooting/`

### 한계와 후속 과제
→ 참고: `docs/mvp.md`(MVP 제외 절), `docs/adr/006-source-registration-scope.md`(후속 소스 등록 방식), `docs/adr/011-kisa-detection-priority.md`(미탐지/미매핑 항목)

## 참고

- 원본 요구사항 기준 문서(`docs/원본_요구사항목록.docx`)는 저장소에 커밋하지 않으므로 발표 자료에는 위 목록의 파생 문서를 인용한다.
- 참고 경로는 이 문서를 작성한 시점(2026-08-26)의 저장소 상태를 기준으로 확인했다. 문서가 이동하거나 이름이 바뀌면 이 목록도 함께 갱신한다.
