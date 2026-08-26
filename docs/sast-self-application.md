# SAST/보안 관점의 자기 적용 근거

이 문서는 SecScan을 만드는 과정 자체에 정적 분석(SAST)과 보안 설계 관점을 어떻게 적용했는지 근거를 모은다. 토이프로젝트 완료 조건 중 "배운 정적 분석 관점을 프로그램 자체에 적용"을 발표에서 바로 증거와 함께 제시하기 위한 목적으로 작성한다.

각 행은 실제 저장소 파일을 열어 확인한 내용만 기록한다. 실제로 실행되지 않는 계획이나 문서상 서술만 있는 항목은 포함하지 않는다.

| 관점 | 적용 위치 | 증거 |
|---|---|---|
| 정적 분석으로 이 프로젝트 자신의 코드를 검사 | CodeQL이 backend(Python)와 frontend(javascript-typescript)를 언어별로 스캔 | `.github/workflows/codeql.yml` — `push`/`pull_request`(main)와 매주 월요일 스케줄, `matrix.language: [python, javascript-typescript]` |
| 시크릿 유출 정적 탐지 | gitleaks로 저장소 전체 커밋 이력을 스캔 | `.github/workflows/ci.yml`의 `security` job, "Secret scan (gitleaks)" 단계(`gitleaks detect --source . --redact -v`). 이 단계는 `continue-on-error`가 없어 탐지되면 CI가 실패한다 |
| 의존성 취약점 정적 점검 | 백엔드는 `pip-audit`, 프론트는 `npm audit`로 알려진 취약 패키지를 점검 | `.github/workflows/ci.yml`의 `security` job. 현재는 `continue-on-error: true`로 실패해도 CI를 막지 않으며, 실제 실패 처리 전환 시점은 `docs/development-workflow.md`(E7-07)에 명시 |
| 의존성 최신화를 통한 지속적 취약점 관리 | Dependabot이 pip/npm/Docker 베이스 이미지/GitHub Actions 의존성을 매주 점검하고 업데이트 PR을 생성 | `.github/dependabot.yml`. 정책 근거는 `docs/adr/012-external-component-security.md`(외부 구성요소 버전 고정·취약점 점검·업데이트 기록 요구) |
| 최소 권한과 실패 시 차단(fail-closed) 원칙 | 비인가 프로젝트/분석/진단 자원 요청은 존재 여부를 노출하지 않고 404, 인증 실패는 401, 역할 권한 부족은 403으로 응답 | `docs/adr/008-unauthorized-response-policy.md`. API 계약에도 "권한이 없는 프로젝트 자원은 404로 응답한다" 명시 — `docs/api-contract.md` |
| 정보 은닉(민감 필드 역할별 분리) | 관리자/일반 사용자 응답 스키마를 `AnalysisUserOut`/`AnalysisAdminOut`으로 분리하고, `error_code`·`error_message`·실행 로그·`raw_result`는 관리자 전용 필드로 제외 | `docs/adr/009-role-based-response-schema.md`. `source_snapshot_location`은 어떤 API 응답에도 포함하지 않는 것도 같은 원칙 — `docs/api-contract.md` |
| 사용자 입력 서버 경로 신뢰 금지 | 프로젝트 생성 시 관리자가 소스 위치를 직접 입력하지 않고, 업로드 성공 후 시스템이 관리하는 위치값을 `source_location`에 기록. 향후 기관 내부 경로 지원 시에도 임의의 서버 경로를 그대로 열지 않고 허용된 루트·접근 권한을 검증하기로 사전에 결정 | `docs/adr/006-source-registration-scope.md` |
| 분석 결과 무결성과 감사 추적성 | 진단 기준(KISA_CATALOG)을 나중에 수정해도 과거 분석 결과가 소급 변경되지 않도록, Finding에 분석 시점의 항목명·신뢰도·언어·조치 권고를 스냅샷으로 복사 저장 | `docs/adr/005-finding-snapshot.md`, `docs/adr/007-recommendation-source.md` |
| 분석 결과의 정직한 표시(과잉 주장 방지) | KISA 49개 항목을 모두 카탈로그로 관리하되 실제 탐지 여부를 `지원`/`부분 지원`/`미지원`으로 구분 표시하고, 외부 도구 결과가 KISA 항목에 매핑되지 않으면 버리지 않고 `미매핑` 상태로 보존 | `docs/adr/011-kisa-detection-priority.md` |
| 변경 관리 통제(브랜치 보호) | `main` 직접 push 금지, PR만 허용, 병합 전 CI(backend/frontend/security/docker) 전체 통과 필수, force push와 브랜치 삭제 금지 | `docs/development-workflow.md` 2절 |

## 참고

- 위 CI 항목은 모두 `.github/workflows/`에 실제로 구성되어 있으며 `main` push와 PR에서 실행된다(스케줄 job인 CodeQL 주간 스캔 제외).
- `security` job의 의존성 감사(`pip-audit`, `npm audit`)는 현재 `continue-on-error: true`이므로, 발표에서는 "탐지는 하되 아직 빌드를 차단하지는 않는다"는 점을 정확히 설명해야 한다.
- 이 문서는 구현이 진행됨에 따라 실제 파일 경로가 바뀌면 함께 갱신한다.
