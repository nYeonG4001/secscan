# ADR-007: 조치 권고의 기준값과 분석 시점 값 보존

## Context

DAR-006은 진단 결과에 조치 권고를 저장하도록 요구한다. KISA 항목별 기본 권고는 공통으로 재사용할 수 있지만, 분석 결과는 과거 시점의 내용을 재현할 수 있어야 한다.

## Decision

KisaCatalog에 항목의 기본 조치 권고를 저장하고, Finding에도 분석 시점에 적용된 `recommendation`을 스냅샷으로 저장한다. Finding의 권고는 카탈로그 변경에 영향을 받지 않는다.

탐지 근거는 Finding의 `evidence`에 저장하고, 분석 도구가 반환한 원본 결과는 Finding의 `raw_result`에 저장한다. Analysis의 `raw_result`는 Finding 목록을 중복 보관하지 않는 안전한 실행 메타데이터 보존용으로 유지한다. 구체적인 원본 결과 범위와 정규화 실패 처리 규칙은 ADR-034를 따른다.

## Consequences

- 카탈로그는 기본 권고를 제공할 수 있다.
- 과거 Finding은 분석 당시 권고와 근거를 재현할 수 있다.
- 결과 저장 시 카탈로그 기본값을 Finding 스냅샷으로 복사하는 정규화 단계가 필요하다.
