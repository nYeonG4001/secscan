# Troubleshooting: E5 로컬 Semgrep 샌드박스 검증 환경

## 기본 정보

- 작성일: 2026-09-01
- 작성자: Codex
- 관련 에픽: E5, E7
- 관련 요구사항: SFR-010, SFR-011, TST-004, TST-005
- 관련 PR 또는 커밋: 없음
- 환경: 로컬

## 문제 요약

macOS Codex 샌드박스에서 고정 Semgrep OSS 1.95.0의 기본 인증서·로그 경로와
`RLIMIT_AS` 제한 때문에 `SemgrepRunner` 기반 fixture 검증이 실행되지 않았다.

## 증상

직접 실행은 기본 인증서 저장소를 찾지 못했고, 실행기는 macOS의 주소 공간 제한에서
`ANALYSIS_RESOURCE_LIMIT`로 종료됐다.

```text
Failure("ca-certs: empty trust anchors.")
ValueError: current limit exceeds maximum limit
```

## 재현 방법

1. macOS Codex 샌드박스에서 Semgrep OSS 1.95.0을 기본 환경 변수로 실행한다.
2. `SemgrepRunner`가 `RLIMIT_AS`를 설정한 뒤 fixture를 실행한다.
3. 인증서·로그 경로 또는 주소 공간 제한에서 실행이 종료된다.

## 기대 결과

고정 YAML과 `--no-rewrite-rule-ids`를 사용한 fixture 검증이 Semgrep 결과를 반환해야 한다.

## 실제 결과

기본 로컬 실행은 위 환경 제약 때문에 결과를 반환하지 못했다. 규칙 YAML 문법이나 fixture의
source-to-sink 형태가 원인은 아니었다.

## 원인 분석

- 확인한 증거: `SSL_CERT_FILE=/etc/ssl/cert.pem`과 임시 Semgrep 로그·설정 경로를 지정하면 직접 Semgrep 실행이 가능했다. 같은 규칙은 Docker의 Python 3.12 검증 환경에서 E5 pytest를 통과했다.
- 원인: macOS 샌드박스가 기본 Semgrep 사용자 로그 경로 접근을 차단하고, 해당 환경의 `RLIMIT_AS` 설정이 실행기와 호환되지 않았다.
- 원인이 아니었던 가설: ADR-040 규칙 YAML 문법, 신규 fixture의 예상 `check_id`, KISA 매핑.

## 해결 방법

- 변경 파일: 없음
- 변경 내용: 직접 검증에는 임시 인증서·Semgrep 상태 경로를 지정하고, 실행기 통합 검증은 고정 Semgrep이 포함된 일회성 Docker 컨테이너에서 수행했다. 제품의 자원 제한 정책은 변경하지 않았다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [ ] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
semgrep 1.95.0 --config semgrep-rules/secscan-security.yml \
  --no-rewrite-rule-ids --json --quiet --oss-only --metrics=off <fixture>

docker run --rm ... secscan-e5-validation-backend:local \
  python -m pytest -q tests/test_e5_result_normalization.py
```

## 남은 위험과 후속 작업

- 남은 문제: macOS 네이티브 `SemgrepRunner` fixture 검증은 `RLIMIT_AS` 호환성을 해결하기 전까지 CI 통과 근거로 사용하지 않는다.
- 후속 작업: Ubuntu GitHub Actions의 필터 없는 `pytest -q`에서 동일 fixture를 재확인한다.
- 관련 문서 업데이트: `docs/epic/e7-sast-evaluation-plan.md`, `backend/semgrep-rules/RULES_PROVENANCE.md`

## 참고 자료

- 로그 경로: `/tmp/secscan-adr040-semgrep.log`
- 화면 캡처: 없음
- 관련 커밋: 없음
