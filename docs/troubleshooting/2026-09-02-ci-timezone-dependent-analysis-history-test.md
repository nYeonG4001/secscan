# Troubleshooting: 분석 이력 행 테스트의 CI 시간대 의존성

## 기본 정보

- 작성일: 2026-09-02
- 작성자: Codex
- 관련 에픽: E6, E7
- 관련 요구사항: TST-007, TST-008
- 관련 PR 또는 커밋: PR #48, `87690ad`
- 환경: GitHub Actions Ubuntu

## 문제 요약

분석 이력 행의 키보드 접근성 테스트가 로컬 KST 시간을 고정해 GitHub Actions UTC에서 실패했다.

## 증상

```text
Unable to find an accessible element with the role "row" and name
/2026-08-30 18:00 분석 완료 2026-08-30 18:01 2026-08-30 18:02/
```

## 재현 방법

1. `frontend`에서 `TZ=UTC npm test -- --run`을 실행한다.
2. `src/App.test.tsx`의 분석 이력 행 테스트를 확인한다.

## 기대 결과

시간대와 무관하게 분석 이력의 요청·시작·완료 열과 키보드 이동 동작을 검증한다.

## 실제 결과

동일한 UTC 시각이 로컬 KST에서는 `18:00`으로, GitHub Actions UTC에서는 `09:00`으로 렌더링돼 고정 행 이름 기대값이 실패했다.

## 원인 분석

- 확인한 증거: PR #48 Frontend build 로그와 `frontend/src/App.test.tsx`의 고정 시각 정규식
- 원인: 화면의 지역 시간 변환을 테스트가 환경 독립적인 값으로 정규화하지 않았다.
- 원인이 아니었던 가설: 분석 이력 API 응답, 상태 라벨, 행의 `tabindex`와 키보드 이동 동작

## 해결 방법

- 변경 파일: `frontend/src/App.test.tsx`
- 변경 내용: 시간대가 변하는 시각 문자열 대신 안정적인 상태 라벨로 분석 이력 행을 찾는다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
TZ=UTC npm test -- --run
npm run lint
npm run typecheck
npm run build
```

## 남은 위험과 후속 작업

- 남은 문제: 시간 표시 형식 자체의 국제화 테스트는 별도 요구사항이 생길 때 추가한다.
- 후속 작업: 없음
- 관련 문서 업데이트: PR 검증 결과

## 참고 자료

- 로그 경로: PR #48 Frontend build
- 화면 캡처: 없음
- 관련 커밋: 후속 수정 커밋에 기록
