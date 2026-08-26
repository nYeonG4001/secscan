# SecScan ERD (MVP 기준)

이 ERD는 docs/mvp.md에 정의된 MVP 7개 기능만 반영합니다. MVP 제외 기능(대시보드 시각화, 이력 비교 등)의 엔티티는 포함하지 않았습니다.

```mermaid
erDiagram
    USER ||--o{ PROJECT : creates
    USER ||--o{ PROJECT_ACCESS : has
    USER ||--o{ ANALYSIS : executes
    PROJECT ||--o{ PROJECT_ACCESS : grants
    PROJECT ||--o{ ANALYSIS : contains
    ANALYSIS ||--o{ FINDING : produces
    KISA_CATALOG ||--o{ FINDING : classifies

    USER {
        int id PK
        string email
        string password_hash
        string role "ADMIN or USER"
    }
    PROJECT {
        int id PK
        string name
        text description
        string source_type
        string target_languages
        string source_location
        int created_by FK
        datetime created_at
        datetime updated_at
    }
    PROJECT_ACCESS {
        int id PK
        int project_id FK
        int user_id FK
        datetime granted_at
        int granted_by FK
    }
    ANALYSIS {
        int id PK
        int project_id FK
        int executed_by FK
        string status "PENDING/RUNNING/COMPLETED/FAILED"
        datetime created_at
        datetime started_at
        datetime completed_at
        text error_message
        jsonb summary "분석 실행 요약"
        jsonb raw_result "semgrep 원본 출력"
    }
    FINDING {
        int id PK
        int analysis_id FK
        string kisa_code FK
        string rule_name "분석 시점 스냅샷, ADR-005"
        string severity
        string confidence
        string language
        string file_path
        int line
        string message
        text evidence
        text recommendation "분석 시점 스냅샷"
        jsonb raw_result "진단 원본 결과"
        text code_snippet
    }
    KISA_CATALOG {
        string kisa_code PK
        string criterion_id
        string item_number
        string category
        string name
        text description
        text reference_info
        string default_severity
        boolean active
        string implementation_status "지원/부분 지원/미지원, ADR-011"
        string semgrep_rule_id "NULL 가능"
        text recommendation "기본 조치 권고"
    }
```

`PROJECT_ACCESS(project_id, user_id)` UNIQUE 제약.

## MVP 기능 ↔ 엔티티 매핑

| MVP 기능 | 관련 엔티티 |
|---|---|
| 1. 인증/인가 | USER |
| 2. 프로젝트 관리 | PROJECT, PROJECT_ACCESS |
| 3. 코드 업로드 | PROJECT, ANALYSIS |
| 4. 정적 분석 실행 | ANALYSIS, KISA_CATALOG (ADR-003) |
| 5. 분석 상태 관리 | ANALYSIS.status, error_message |
| 6. 결과 조회 | FINDING (스냅샷 필드, ADR-005) |
| 7. 기본 보안 | USER.password_hash, PROJECT_ACCESS(권한 체크), ANALYSIS(경로 검증) |
