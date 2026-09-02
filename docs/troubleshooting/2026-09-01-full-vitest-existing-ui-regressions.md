# Troubleshooting: 전체 Vitest의 기존 화면 회귀

## 기본 정보

- 작성일: 2026-09-01
- 작성자: Codex
- 관련 에픽: E3-09 검증 중 발견
- 관련 요구사항: TST-004, SFR-007
- 관련 PR 또는 커밋: 없음
- 환경: 로컬 프런트엔드

## 문제 요약

ZIP 사전검증 Drawer 테스트는 통과하지만, 전체 Vitest는 기존 `FindingsPage`·`CatalogPage` 변경과 프로젝트 행동 문구 변경 때문에 실패한다.

## 증상

```text
44 tests: 36 passed, 8 failed, 1 unhandled error
TypeError: detailRef.current?.scrollTo is not a function
```

## 재현 방법

1. `frontend` 디렉터리에서 `npm test`를 실행한다.
2. `src/pages/E6Pages.test.tsx`와 `src/App.test.tsx` 결과를 확인한다.

## 기대 결과

전체 Vitest가 jsdom 환경에서 실행되고, 프로젝트 상세 화면 테스트가 현재 버튼 문구와 행동을 검증한다.

## 실제 결과

`FindingsPage.tsx`와 `CatalogPage.tsx`의 `scrollTo` 호출이 jsdom에 없는 메서드를 직접 호출한다. 또한 `App.test.tsx`가 현재 화면의 `분석` 버튼 대신 이전 `소스` 버튼과 중간 행동 Drawer를 기대한다.

## 원인 분석

- 확인한 증거: `src/pages/FindingsPage.tsx:58`, `src/pages/CatalogPage.tsx:116`, `src/App.test.tsx:305`의 실패 출력.
- 원인: ZIP 사전검증과 별개인 미커밋 UI 변경이 jsdom 호환 가드 및 기존 테스트 기대값을 함께 갱신하지 않았다.
- 원인이 아니었던 가설: `src/pages/SourceUploadDrawer.test.tsx`의 ZIP 사전검증 9개는 같은 실행에서 모두 통과했다.

## 해결 방법

- 변경 파일: 없음
- 변경 내용: 사용자가 보존을 요청한 범위 밖 UI 변경이므로 이번 작업에서 덮어쓰거나 되돌리지 않았다.

## 검증

- [x] 같은 재현 절차로 문제를 확인함
- [x] 관련 단위 테스트 통과
- [ ] 관련 통합 또는 화면 테스트 통과
- [ ] 기존 기능 회귀 없음
- [x] 보안 영향 확인

```text
npm test
SourceUploadDrawer.test.tsx: 9 passed
전체: 36 passed, 8 failed, 1 unhandled error
```

## 남은 위험과 후속 작업

- 남은 문제: 전체 프런트엔드 회귀가 통과하지 않는다.
- 후속 작업: `scrollTo`의 jsdom 호환 처리와 프로젝트 행동 테스트를 UI 변경 의도에 맞춰 별도 검토·수정한다.
- 관련 문서 업데이트: 이 문서

## 참고 자료

- 로그 경로: 없음
- 화면 캡처: 없음
- 관련 커밋: 없음
