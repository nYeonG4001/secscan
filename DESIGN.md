# Design

## Source of truth
- Status: Active
- Last refreshed: 2026-08-28
- E0 visual baseline: `docs/design/drafts/secscan-ui-v0.5.pen`. 이 파일은 Git에 저장하지 않으며, 이후 화면 변경은 구현 중 확인된 요구사항 문제에 한해 최소 범위로 진행한다.
- Primary product surfaces: 로그인, 프로젝트 관리, 소스 업로드와 분석 실행, 분석 상태, 진단 결과, KISA 카탈로그
- Evidence reviewed: 별도 보관 원본 요구사항 DOCX, `frontend/src/App.tsx`, `frontend/src/pages/`, `frontend/tailwind.config.ts`, `docs/design/drafts/secscan-login-v0.2.pen`, `docs/design/drafts/secscan-ui-v0.5.pen`, 사용자가 제공한 Snyk 랜딩 캡처와 제품 데모 영상. Snyk 자료는 정보 구조를 복사하지 않고 다크 톤과 시각적 밀도 참고용으로만 사용한다.

## Brand
- Personality: 보안 도구답게 신뢰감 있고 명확하며, 검은 캔버스와 강한 타이포로 집중도를 주는 인터페이스
- Trust signals: 분석 상태, 실행자, 시간, 탐지 근거를 명확히 표시하고 내부 오류와 원본 로그는 권한에 따라 제한
- Avoid: 장식적인 대시보드, 의미 없는 그래프, 모든 요소에 네온 효과를 주는 처리, 데이터 화면을 비워 보이게 만드는 과도한 여백

## Product goals
- Goals: 분석 흐름과 결과를 이해하기 쉽게 제공하고 권한과 오류 상태를 명확히 전달
- Non-goals: MVP에서 대시보드 시각화·PDF 보고서·알림 구현
- Success signals: 사용자가 업로드부터 결과 상세 조회까지 막힘없이 완료

## Personas and jobs
- Primary personas: 시스템 관리자, 권한 있는 일반 사용자
- User jobs: 관리자는 분석 실행, 일반 사용자는 허용된 프로젝트 결과 확인
- Key contexts of use: 데스크톱 브라우저 중심의 교육·검수 환경

## Information architecture
- Primary navigation: 프로젝트, 진단 기준
- Core routes/screens: `/login`, `/projects`, `/projects/:projectId`, `/projects/:projectId/analyses/:analysisId`, `/catalog`. 소스 등록 패널은 `/projects/:projectId` 안에서 열고, 분석 상세 경로는 진행 또는 실패 상태에서는 상태 화면을, 완료 상태에서는 결과 화면을 표시한다.
- Content hierarchy: 현재 프로젝트와 분석 상태를 먼저 보여주고 상세 근거와 조치 권고를 단계적으로 노출
- Navigation by role: ADMIN과 USER 모두 프로젝트와 진단 기준 메뉴를 본다. 분석 실행, 분석 이력, 분석 결과는 선택한 프로젝트 안에서 제공한다.
- Login: 비인증 화면은 전역 메뉴 없이 이메일과 비밀번호 입력만 제공한다. MVP는 내부 계정 로그인만 지원하며, 로그인 성공 후 사용자는 프로젝트 목록으로 이동한다.
- Project list by role: ADMIN은 모든 프로젝트를 조회하고 새 프로젝트 버튼을 본다. USER는 접근권한이 부여된 프로젝트만 조회하며, 새 프로젝트 버튼을 렌더링하지 않는다.
- Project actions: 프로젝트 행에서 프로젝트 정보, 사용자 접근권한 관리, 소스 등록과 분석 실행, 최근 분석 상태 확인으로 이동할 수 있다.
- Project detail: 프로젝트 상세는 탭 없이 한 화면으로 구성한다. 프로젝트 정보, 최근 분석 상태, 분석 이력을 한 번의 스크롤 안에서 제공하고, 완료된 분석을 선택하면 결과를 확인한다.
- Role-specific actions: 소스 등록과 분석 실행, 사용자 접근권한 관리는 ADMIN에게만 렌더링한다. USER에게는 비활성화된 버튼을 보여주지 않는다.
- Project list status: 소스 상태는 `등록 필요`, `등록됨`으로, 최근 분석 상태는 `분석 전`, `분석 대기`, `분석 진행 중`, `분석 완료`, `분석 실패`로 표시한다.
- Findings: 기본 정렬은 심각도 높은 순이다. 상세 패널은 심각도와 진단 항목명을 먼저, 파일 경로와 줄 번호를 다음으로 표시한다. KISA 매핑 여부와 무관하게 ADMIN은 원본 분석 결과를 확인할 수 있고, USER에게는 원본 분석 결과를 렌더링하지 않는다.
- Catalog management: 공식 KISA 49개 항목은 초기 시드로 제공한다. ADMIN은 목록에서 항목을 선택해 오른쪽 상세 패널에서 수정하고, 신규 진단 기준을 등록할 수 있다. 같은 `kisa_code`의 중복 등록은 허용하지 않는다. USER는 같은 목록과 상세를 읽기 전용으로 조회한다.
- Action drawers: 소스 등록과 분석 실행, 진단 기준 등록, 프로젝트 생성, 사용자 접근권한 관리는 오른쪽 액션 패널로 연다. 결과와 카탈로그의 조회 상세 패널에는 이 규칙을 강제하지 않는다.

## Design principles
- 상태 우선: 분석 상태와 다음 행동을 항상 명확히 표시
- 근거 우선: 진단 결과는 위치·메시지·탐지 근거를 함께 제공
- 권한 명확성: 사용자가 할 수 없는 작업은 이유와 함께 비활성화 또는 차단
- Tradeoffs: 시각적 장식보다 정보 밀도와 읽기 쉬운 보안 정보를 우선

## Visual language
- Color: 캔버스는 거의 검은색, 표면은 한 단계 밝은 차콜을 사용한다. 기본 글자는 밝은 흰색, 보조 글자는 회보라 계열을 사용한다. 보라와 핑크, 청록은 활성 메뉴와 핵심 행동을 위한 브랜드 포인트로만 쓴다. 성공, 경고, 실패 상태 색상은 브랜드 포인트와 구분한다.
- Color candidates: canvas `#080808`, surface `#121214`, border `#2A2A2F`, foreground `#F5F5F5`, muted `#A0A0AA`, violet `#B45CFF`, magenta `#F05CFF`, cyan `#39D9CE`. 구현 전에 `secscan-ui-v0.5`에서 대비를 확인한다.
- Typography: 페이지 제목은 크고 굵은 흰 글자로, 표와 폼의 정보는 작고 조밀한 글자로 계층을 분명하게 나눈다. 큰 제목은 화면과 섹션의 시작에만 사용한다.
- Spacing/layout rhythm: 프로젝트 목록과 결과 목록은 넓은 작업 영역을 사용한다. 입력 폼과 상세 정보는 필요한 폭만 차지하며, 빈 공간을 채우기 위한 보조 카드는 만들지 않는다.
- Shape/radius/elevation: 표면은 얇은 차콜 테두리와 작은 라운드로 구분한다. 선택된 메뉴와 주요 패널에는 은은한 보라 테두리 또는 배경을 사용하되, 강한 그림자와 광원 효과는 최소화한다.
- Motion: 상태 폴링과 로딩 표시 정도로 제한한다. 보라 포인트는 활성 상태 전환에 짧고 절제된 변화로만 사용한다.
- Imagery/iconography: 의미 전달에 필요한 아이콘만 사용한다. 랜딩 페이지의 장식용 광원, 점 패턴, 대형 그래픽은 업무 데이터 화면에 사용하지 않는다.

## Components
- Existing components to reuse: Tailwind 기반 버튼, 입력, 카드, 표 스타일
- New/changed components: AppShell, GlobalNavigation, LoginForm, ProtectedRoute, RoleGuard, StatusBadge, ProjectActionMenu, ActionDrawer, FindingTable, FindingDetail, RecommendationBlock, CatalogDetailPanel, EmptyState, ErrorState
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
- Error: 일반 사용자는 일반적인 실패 안내를 보고, 관리자는 허용된 상세 오류 정보를 확인하며 재시도 방법을 제공한다. 인증 실패 또는 만료(401)는 `로그인 정보가 만료되었거나 유효하지 않습니다. 다시 로그인해 주세요.` 안내 뒤 로그인 화면으로 이동한다. 관리자 전용 기능 요청 거부(403)는 `이 기능은 관리자만 사용할 수 있습니다.`를, 프로젝트 자원 미발견 또는 비인가(404)는 `요청한 정보를 찾을 수 없습니다.`를 표시한다. 소스 업로드 오류는 코드별로 `25MB 이하 ZIP만 업로드할 수 있습니다.`, `ZIP 압축 해제 제한을 초과했습니다.`, `안전하지 않은 ZIP입니다.`, `지원하는 소스 파일이 없습니다.`, `분석이 끝난 뒤 업로드할 수 있습니다.`, `다른 업로드가 진행 중입니다.`, `업로드에 실패했습니다. 다시 시도해 주세요.` 중 하나만 짧게 표시하며 내부 경로와 서버 예외는 표시하지 않는다.
- Success: 로그인 성공 후 프로젝트 목록으로 이동하고, 업로드·권한 변경·분석 완료 결과를 확인 가능하게 표시
- Disabled: 권한 부족 기능은 USER에게 렌더링하지 않는다. 프로젝트에 `PENDING` 또는 `RUNNING` 분석이 있으면 ADMIN의 소스 등록 및 분석 실행 버튼을 비활성화하고, 완료 또는 실패 후 다시 실행할 수 있다는 안내를 표시한다.
- Source upload: ADMIN은 파일 선택, 업로드 진행률, 취소, 실패, 성공 상태를 구분해 본다. 자동 재시도는 하지 않고 사용자가 다시 시도한다. 취소 뒤에는 프로젝트 상태를 다시 조회해 실제 소스 등록 여부를 확인한다.
- Action drawer: 폭은 400px로 고정한다. 헤더는 64px, 제목은 16px, 오른쪽에는 X 닫기 버튼을 둔다. 헤더와 완료 버튼 영역은 고정하고 본문만 독립 스크롤한다. 패널이 열리면 헤더 아래의 메인 영역을 같은 검은 반투명 오버레이로 어둡게 처리하고, 메인 영역의 클릭과 스크롤을 잠근다. `Esc`로 닫고 기존 메인 스크롤 위치를 복원한다.
- Button hierarchy: 기본 행동은 흰 배경과 검은 글자, 보조 행동은 차콜 배경과 테두리, 위험 행동은 빨간 글자 또는 테두리로 통일한다. 기본과 보조 버튼은 8px 라운드와 14px 글자를 사용한다.
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
- [x] 결과 상세에는 권한 있는 사용자가 취약 줄 주변 코드 일부를 조회한다.
- [x] 관리자 분석 소스 뷰어는 E1부터 E7까지 완료한 뒤 시간이 남을 때만 구현하는 선택 작업으로 둔다. 현재 MVP 완료 조건에서는 제외한다.
- [x] 관리자와 일반 사용자 모두 로그인 성공 후 프로젝트 목록으로 이동한다.
- [ ] 모바일 화면을 지원할 범위
- [x] 로그인은 SecScan 브랜드의 이메일과 비밀번호 기반 내부 계정 인증으로 확정한다. 소셜 로그인, 회원가입, 비밀번호 재설정은 MVP 화면에 포함하지 않는다. 인증 세션은 최대 24시간 유지하고, 유휴 시간 만료는 후속 보안 고도화로 둔다.
- [x] MVP 소스 등록은 파일 업로드만 지원하고, Git 저장소와 기관 내부 경로는 후속 범위로 둔다. source_location은 검증된 시스템 관리 값으로 사용
- [x] 조치 권고는 KisaCatalog 기본값과 Finding 분석 시점 스냅샷으로 분리
- [x] 프로젝트 자원 비인가 접근은 404, 인증 실패는 401, 일반 관리자 기능 권한 부족은 403으로 처리
- [x] 분석 응답은 사용자용과 관리자용 스키마로 분리
- [x] 프로젝트의 분석 대상 언어는 소스 등록 시 자동 식별한다. 프로젝트 생성 화면에는 언어 선택을 두지 않고, 감지 결과를 프로젝트 정보에 표시한다.
