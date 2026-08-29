# Troubleshooting: E5 Semgrep 실행기의 스냅샷 작업 디렉터리 모듈 탐색 실패

## 기본 정보

- 작성일: 2026-08-29
- 작성자: Codex
- 관련 에픽: E4, E5
- 관련 요구사항: SFR-010, SFR-011, SFR-012, TST-005
- 관련 PR 또는 커밋: 없음
- 환경: Docker

## 문제 요약

Semgrep 실행기가 분석 시점 스냅샷 디렉터리를 작업 디렉터리로 사용하면 Python이
`app.services.semgrep_wrapper` 모듈을 찾지 못해 분석이 실패했다.

## 증상

실제 Java, JavaScript, Python fixture를 `SemgrepRunner`로 분석하는 E5 테스트가
모두 `ENGINE_EXECUTION_FAILED`로 실패했다.

```text
Error while finding module specification for 'app.services.semgrep_wrapper'
(ModuleNotFoundError: No module named 'app')
```

## 재현 방법

1. Semgrep이 설치된 백엔드 Docker 이미지에서 `SemgrepRunner.run(snapshot_root)`를 실행한다.
2. 실행기가 `cwd=snapshot_root`로 `python -m app.services.semgrep_wrapper`를 시작한다.
3. 백엔드 루트가 `PYTHONPATH`에 없으면 모듈 탐색에 실패한다.

## 기대 결과

분석 실행기는 스냅샷을 현재 작업 디렉터리로 사용하면서도 Semgrep 제한 래퍼를 실행하고,
고정 YAML 규칙의 결과를 JSON으로 반환한다.

## 실제 결과

스냅샷 디렉터리가 Python의 모듈 탐색 기준이 되어 백엔드의 `app` 패키지를 찾지 못했고,
Semgrep 시작 전 분석이 실패했다.

## 원인 분석

- 확인한 증거: `backend/app/services/semgrep_runner.py`가 `cwd=snapshot_root`로
  subprocess를 시작하고 `python -m app.services.semgrep_wrapper`를 호출했다.
- 원인: subprocess 환경에 백엔드 루트가 `PYTHONPATH`로 전달되지 않았다.
- 원인이 아니었던 가설: Semgrep CLI 미설치. 일반 Python 테스트 컨테이너에는 CLI가 없었지만,
  E4 런타임 이미지는 Semgrep OSS 1.95.0을 포함하고 있었다.

## 해결 방법

- 변경 파일: `backend/app/services/semgrep_runner.py`
- 변경 내용: subprocess 실행 환경의 `PYTHONPATH` 앞에 백엔드 루트를 추가했다. 스냅샷 디렉터리를
  계속 작업 디렉터리로 유지하므로 Semgrep 결과 경로는 상대 경로로 생성된다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
SemgrepRunner 직접 실행 결과:
secscan.java.runtime-exec
secscan.javascript.eval
secscan.python.pickle-loads

pytest -q tests/test_e5_result_normalization.py tests/test_semgrep_runner.py \
  tests/test_analysis_execution.py
20 passed

pytest -q
208 passed, 5 warnings

ruff check app tests
All checks passed
```

## 남은 위험과 후속 작업

- 남은 문제: 없음.
- 후속 작업: 새 분석 실행기가 스냅샷 디렉터리를 작업 디렉터리로 사용하면 같은 환경 전달 원칙을 유지한다.
- 관련 문서 업데이트: 없음.

## 참고 자료

- 로그 경로: 현재 E5 구현 작업 세션의 Docker 테스트 출력
- 화면 캡처: 없음
- 관련 커밋: 없음
