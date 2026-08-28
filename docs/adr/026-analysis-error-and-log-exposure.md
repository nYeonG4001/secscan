# ADR-026: 분석 오류와 실행 로그의 제한적 보존

**Context**: DAR-005는 분석 오류 정보와 실행 요약 저장을 요구하고, SEC-003과 SEC-009는 분석 오류와 실행 로그를 관리자 권한으로 제한한다. E4의 Semgrep 실행 오류에는 내부 스냅샷 절대 경로나 업로드 원본 파일명이 포함될 수 있어, 단순히 모든 표준 오류를 저장하거나 응답으로 내보내면 서버 구조가 노출될 수 있다.

**Decision**: `ANALYSIS`에 관리자 전용 `execution_log` 텍스트 필드를 추가한다. 로그는 Semgrep 표준 오류와 실행 단계 정보만 저장하며, 최근 64 KiB를 초과하지 않게 제한한다. Semgrep은 분석 스냅샷 디렉터리를 현재 작업 디렉터리로 사용하고 상대 경로 `.`만 분석 대상으로 전달해, 절대 서버 경로가 처음부터 표준 오류에 나타나지 않도록 한다. 문자열 스크러빙은 저장 전 보조 방어로만 사용한다.

실패 원인은 `ANALYSIS_TIMEOUT`, `ANALYSIS_RESOURCE_LIMIT`, `SOURCE_SNAPSHOT_FAILED`, `ENGINE_EXECUTION_FAILED`, `ENGINE_OUTPUT_INVALID`, `ANALYSIS_INTERRUPTED`의 안정적인 `error_code`로 기록한다. `error_message`에는 안전하게 정리한 상세 원인을, `raw_result`에는 안전한 실행 메타데이터를 분리해 저장한다. 완료 분석의 Finding 원본 결과와 정규화 실패 시 전체 실패 처리는 ADR-034를 따른다.

일반 사용자 응답에는 `FAILED` 상태와 “분석을 완료하지 못했습니다. 관리자에게 문의하세요.” 안내만 제공한다. 관리자 응답에는 `error_code`, `error_message`, 제한된 `execution_log`를 제공한다. 서버 내부 경로, 실행 명령, 환경변수, 업로드 원본 파일명은 저장과 모든 API 응답에서 제외한다.

**Alternatives**: Semgrep 표준 오류 전체를 DB에 저장, 로그 파일 경로만 저장, 오류 메시지만 저장, 제한된 관리자용 진단 로그를 DB에 저장

**Consequences**: 관리자는 실패 원인을 API에서 확인할 수 있고, 일반 사용자는 내부 운영 정보를 얻을 수 없다. 로그 파일의 별도 보관과 정리 정책 없이도 MVP의 진단 범위를 충족한다. 실행 로그 필드 추가와 Alembic migration, ADMIN/USER 응답 스키마 분리가 필요하다.

**References**: ADR-009, ADR-025, DAR-005, SEC-003, SEC-009
