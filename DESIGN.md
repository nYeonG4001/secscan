# Design

## Source of truth
- Status: Draft
- Last refreshed: 2026-08-25
- Primary product surfaces: 로그인, 프로젝트 관리, 소스 업로드·분석 실행, 분석 상태, 진단 결과, KISA 카탈로그
- Evidence reviewed: `docs/원본_요구사항목록.docx`, `frontend/src/App.tsx`, `frontend/src/pages/`, `frontend/tailwind.config.ts`, `docs/design/drafts/secscan-login-v0.1.pen`

## Brand
- Personality: 보안 도구답게 신뢰감 있고 명확한 인터페이스
- Trust signals: 분석 상태, 실행자, 시간, 탐지 근거를 명확히 표시하고 내부 오류와 원본 로그는 권한에 따라 제한
- Avoid: 장식적인 대시보드, 의미 없는 그래프, 과도한 경고 색상

## Product goals
- Goals: 분석 흐름과 결과를 이해하기 쉽게 제공하고 권한과 오류 상태를 명확히 전달
- Non-goals: MVP에서 대시보드 시각화·PDF 보고서·알림 구현
- Success signals: 사용자가 업로드부터 결과 상세 조회까지 막힘없이 완료

## Personas and jobs
- Primary personas: 시스템 관리자, 권한 있는 일반 사용자
- User jobs: 관리자는 분석 실행, 일반 사용자는 허용된 프로젝트 결과 확인
- Key contexts of use: 데스크톱 브라우저 중심의 교육·검수 환경

## Information architecture
- Primary navigation: 프로젝트, 분석 실행, 분석 이력·결과, KISA 카탈로그
- Core routes/screens: `/login`, `/admin/projects`, `/admin/upload`, `/analyses/:analysisId/status`, `/analyses/:analysisId/findings`, `/catalog`
- Content hierarchy: 현재 프로젝트와 분석 상태를 먼저 보여주고 상세 근거와 조치 권고를 단계적으로 노출

## Design principles
- 상태 우선: 분석 상태와 다음 행동을 항상 명확히 표시
- 근거 우선: 진단 결과는 위치·메시지·탐지 근거를 함께 제공
- 권한 명확성: 사용자가 할 수 없는 작업은 이유와 함께 비활성화 또는 차단
- Tradeoffs: 시각적 장식보다 정보 밀도와 읽기 쉬운 보안 정보를 우선

## Visual language
- Color: 중립적인 회색 기반, 정보·성공·경고·실패 상태에만 의미 있는 색상 사용
- Typography: 기존 Tailwind 기본 글꼴과 크기 체계를 확장
- Spacing/layout rhythm: 카드와 표 중심의 일정한 여백
- Shape/radius/elevation: 기존 Tailwind 스타일을 유지하고 과도한 그림자 사용 금지
- Motion: 상태 폴링과 로딩 표시 정도로 제한
- Imagery/iconography: 의미 전달에 필요한 아이콘만 사용

## Components
- Existing components to reuse: Tailwind 기반 버튼, 입력, 카드, 표 스타일
- New/changed components: AppShell, ProtectedRoute, RoleGuard, StatusBadge, FindingTable, FindingDetail, RecommendationBlock, EmptyState, ErrorState
- Variants and states: loading, empty, error, success, disabled, unauthorized
- Token/component ownership: `frontend/src/index.css`와 Tailwind 설정을 기준으로 관리

## Accessibility
- Target standard: 키보드로 주요 흐름을 완료할 수 있도록 구현
- Keyboard/focus behavior: 입력 순서와 포커스 표시 유지
- Contrast/readability: 상태 색상만으로 의미를 전달하지 않고 텍스트 라벨 병행
- Screen-reader semantics: 표·폼·상태 영역에 적절한 HTML 의미 부여
- Reduced motion and sensory considerations: 자동 갱신은 과도한 애니메이션 없이 표시

## Responsive behavior
- Supported breakpoints/devices: 데스크톱 우선, 태블릿 폭까지 대응
- Layout adaptations: 결과 표는 작은 화면에서 주요 열 우선 표시 및 상세 패널 사용
- Touch/hover differences: hover에만 의존하지 않고 클릭 가능한 요소를 명시

## Interaction states
- Loading: 업로드·분석 실행·폴링 중 진행 상태 표시
- Empty: 프로젝트 없음, 분석 결과 없음, 필터 결과 없음 안내
- Error: 일반 사용자는 일반적인 실패 안내를 보고, 관리자는 허용된 상세 오류 정보를 확인하며 재시도 방법을 제공
- Success: 업로드·권한 변경·분석 완료 결과를 확인 가능하게 표시
- Disabled: 권한 없음 또는 처리 중인 작업의 버튼 비활성화
- Offline/slow network, if applicable: 요청 중복 실행을 막고 timeout 안내

## Content voice
- Tone: 짧고 직접적인 한국어
- Terminology: 원본 요구사항의 용어인 프로젝트, 분석 실행, 진단 결과, 구현 상태 사용
- Microcopy rules: 오류 메시지는 원인과 사용자가 할 수 있는 다음 행동을 함께 안내

## Implementation constraints
- Framework/styling system: React, TypeScript, Vite, Tailwind
- Design-token constraints: 기존 Tailwind 설정을 우선 사용
- Performance constraints: 분석 결과 목록은 로딩 상태와 빈 상태를 제공
- Compatibility constraints: API 오류와 만료된 인증 토큰을 일관되게 처리
- Test/screenshot expectations: 주요 사용자 흐름과 상태별 렌더링을 검증

## Open questions
- [ ] 실제 분석 결과 상세에서 코드 스니펫을 어떤 크기와 형태로 보여줄지
- [ ] 관리자와 일반 사용자에게 제공할 기본 진입 화면
- [ ] 모바일 화면을 지원할 범위
- [ ] 로그인 초안을 SecScan 브랜드와 한국어 문구로 확정할 시점
- [x] 소스 등록은 파일 업로드, Git 저장소, 기관 내부 경로를 지원하는 방향으로 설계하고 source_location은 검증된 시스템 관리 값으로 사용
- [x] 조치 권고는 KisaCatalog 기본값과 Finding 분석 시점 스냅샷으로 분리
- [x] 프로젝트 자원 비인가 접근은 404, 인증 실패는 401, 일반 관리자 기능 권한 부족은 403으로 처리
- [x] 분석 응답은 사용자용과 관리자용 스키마로 분리
