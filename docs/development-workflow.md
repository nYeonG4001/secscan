# SecScan 개발 운영 기준

## 1. 프로젝트 진행 순서

### E0. 디자인과 사용자 흐름

- Pen.dev에서 로그인, 기본 레이아웃, 프로젝트, 업로드, 분석 상태, 결과, 카탈로그 화면을 설계한다.
- 정상 상태뿐 아니라 로딩, 빈 결과, 실패, 권한 없음 상태도 설계한다.
- 화면에 표시할 데이터 필드와 사용자 행동을 확정한다.
- 결정된 UI 원칙은 루트의 `DESIGN.md`에 반영한다.

### 에픽 착수 전 화면과 요구사항 재검토

- E0의 화면 설계는 구현을 위한 현재 기준이며, 원본 요구사항이나 멘토 답변을 대체하는 최종 결정이 아니다.
- 각 에픽을 시작하기 전에 해당 에픽이 사용하는 화면, 데이터 필드, API 계약, ADR을 함께 검토한다.
- 원본 요구사항이 여러 방식으로 해석될 수 있으면 화면을 확정하지 않고, 가정과 영향 범위를 `docs/requirements-interpretation.md`에 기록한 뒤 멘토에게 확인한다.
- 멘토 답변이나 구현 검토로 결정이 바뀌면 관련 화면, `DESIGN.md`, 에픽 작업 상세, API 계약을 함께 갱신한다. 관련 없는 화면을 다시 설계하지 않는다.

### E1. 데이터 모델과 API 계약

- 사용자, 프로젝트, 분석 실행, 진단 결과, 진단 기준 데이터 구조를 확정한다.
- 분석 상태와 실패 정보를 정의한다.
- 공통 진단 결과 형식을 정의한다.
- 모델 변경과 함께 Alembic migration을 작성한다.

### E2. 인증과 권한

- 로그인, 토큰 만료, 관리자와 일반 사용자 권한을 완성한다.
- 프로젝트 소속을 기준으로 분석 실행과 결과 조회를 검증한다.
- 프론트의 메뉴, 버튼, 페이지 접근도 역할에 맞게 제어한다.

### E3. 소스 등록과 업로드 보안

- MVP에서는 파일 업로드와 프로젝트별 작업영역을 구현한다. Git 저장소와 기관 내부 경로는 후속 에픽으로 둔다.
- ZIP 경로 조작, 심볼릭 링크, 비정상 경로 접근을 차단한다.
- 프론트에 허용 파일 형식, 용량, 업로드 진행 상태를 표시한다.

### E4. 분석 실행

- 분석 엔진과 실행 방식을 결정한다.
- Java, JavaScript, Python 분석을 연결한다.
- 분석 작업을 `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`로 관리한다.
- timeout, 자원 제한, 오류 로그 처리를 구현한다.

### E5. 결과 정규화와 KISA 연결

- 분석 결과를 공통 형식으로 변환한다.
- KISA 진단 기준과 분석 결과를 연결한다.
- 심각도, 신뢰도, 파일 위치, 탐지 근거, 조치 권고, 원본 결과를 저장한다.

### E6. 결과와 카탈로그 UI

- 분석 이력, 상태, 결과 목록, 필터, 상세 정보를 구현한다.
- KISA 49개 카탈로그와 구현 상태를 표시한다.
- 실제 결과 데이터로 화면을 검증한다.

### E7. 테스트와 검증 증거

- 인증, 권한, 파일 보안, 분석 처리, 결과 관리 테스트를 작성한다.
- Java, JavaScript, Python별 취약 코드와 정상 코드를 준비한다.
- 요구사항, 테스트, 실행 결과, 화면 또는 로그 증거를 연결한다.

## 2. GitHub 저장소 기준

### 저장소 구성

- 저장소 이름: `secscan` (`https://github.com/nYeonG4001/secscan`)
- 기본 브랜치: `main`
- 저장소 공개 여부: Public. 교육 프로젝트 목적상 LICENSE 파일은 두지 않는다(기본 All rights reserved 유지).
- 비밀값, 실제 사용자 비밀번호, `.env` 파일, 업로드 소스코드는 커밋하지 않는다.
- `README.md`, `DESIGN.md`, `docs/`를 저장소의 공식 설명 자료로 유지한다.

### `main` 브랜치 보호

혼자(+AI 페어) 작업하는 프로젝트라 "승인 리뷰 필수" 같은 GitHub 강제 규칙은 걸지 않는다. 대신 다음만 강제한다.

- `main`에 직접 push 금지, Pull Request만 허용
- PR 병합 전 CI(`backend`, `frontend`, `security`, `docker` job) 전체 통과 필수
- `main`에 force push와 브랜치 삭제 금지

첫 커밋과 첫 push가 있어야 GitHub에 `main` 브랜치가 생기므로, 이 보호 설정은 **첫 push 이후에** 적용한다. "승인 리뷰"는 강제 규칙 대신 `.github/pull_request_template.md`의 자가 점검 체크리스트와 아래 9절의 수동 `/code-review` 절차로 대체한다.

### 브랜치 전략

작은 교육 프로젝트이므로 `main`과 기능 브랜치만 사용한다.

```text
main
├── feat/e1-data-model
├── feat/e2-auth
├── feat/e3-upload
├── feat/e4-analysis
├── feat/e5-result-normalization
├── feat/e6-frontend
└── test/e7-verification
```

- `main`: 항상 실행 가능하고 검증된 상태
- `feat/*`: 기능 개발
- `fix/*`: 버그 수정
- `test/*`: 테스트와 샘플 추가
- `docs/*`: 문서 변경
- 직접 `main`에 커밋하지 않고 Pull Request로 병합한다.

## 3. 커밋 규칙

Conventional Commits 형식을 사용한다. 커밋 타입은 영어로 통일하고, 설명은 한국어로 작성한다.

```text
<type>(<scope>): <한국어 설명>
```

예시:

```text
feat(auth): 만료된 토큰 검증 추가
feat(analysis): 분석 상태 전환 추가
feat(ui): 진단 결과 상세 패널 추가
fix(upload): ZIP 경로 조작 차단
test(auth): 비인가 접근 테스트 추가
docs(requirements): 요구사항 검증표 추가
refactor(result): 결과 정규화 서비스 분리
chore(ci): 백엔드와 프론트 검사 추가
```

규칙:

- 한 커밋에는 하나의 논리적 변경만 포함한다.
- 커밋 메시지는 명령형으로 작성한다.
- 기능 구현과 대규모 포맷 변경을 한 커밋에 섞지 않는다.
- 관련 요구사항 번호를 본문에 기록할 수 있다.

```text
feat(analysis): normalize scanner findings

Refs: SFR-009, SFR-014, DAR-006
```

## 4. Pull Request 기준

기능 브랜치에서 작업한 뒤 Pull Request로 `main`에 병합한다. 작은 프로젝트라도 변경 이유와 검증 결과를 남기는 것을 기준으로 한다.

```text
main
→ feat/e4-analysis 브랜치 생성
→ 기능 구현과 테스트 작성
→ Pull Request 생성
→ GitHub Actions 검사
→ 리뷰와 검증
→ main 병합
→ 배포 또는 Preview 확인
```

PR 하나에는 하나의 기능 목적을 담고, 서로 다른 목적의 변경은 별도 PR로 나눈다. 예를 들어 설치 안내 수정과 랜딩 문구 수정처럼 독립적인 변경은 커밋을 나누고, 필요하면 PR도 나눈다.

혼자 진행하는 프로젝트이므로 에픽 단위 PR은 다음 2개로 제한한다.

1. **설계 PR**: 해당 에픽의 작업 상세, ERD, API 계약, ADR 등 문서 변경
2. **구현 PR**: 해당 에픽의 모든 하위 작업(E1-01~E1-09처럼)을 한 PR에 담는다. 커밋은 작업 번호별로 나눠서 히스토리를 유지하되, PR·CI·머지는 에픽당 한 번만 진행한다.

하위 작업 하나마다 별도 PR을 만들지 않는다. CI는 PR 전체 단위로 통과해야 머지되므로, 하위 작업 하나가 실패하면 그 에픽의 구현 PR 전체가 머지 대기 상태가 된다는 점을 감안한다.

PR 제목도 커밋 형식과 맞춘다.

PR을 생성하면 `.github/pull_request_template.md`가 아래 형식으로 자동 채워진다.

```text
## 변경 내용

## 관련 에픽
- E4

## 관련 요구사항
- SFR-009
- SFR-015

## 검증
- [ ] backend tests
- [ ] frontend build
- [ ] 수동 화면 확인
- [ ] 보안 부정 시나리오 확인

## 화면 또는 실행 증거
```

PR 병합 조건:

- CI 통과
- 관련 테스트 통과
- 요구사항 완료 조건 확인
- 필요하면 화면 캡처 또는 API 응답 첨부

리뷰어가 한 명뿐인 경우에도 작성자가 스스로 다음을 확인한 뒤 병합한다.

- 요구사항 완료 조건 확인
- 변경 파일과 불필요한 변경 확인
- 실패·권한 없음·빈 상태 확인
- CI 전체 통과
- 배포 후 확인할 작업을 PR 본문에 기록

## 5. CI 기준

GitHub Actions는 Pull Request와 `main` push에서 실행한다. `.github/workflows/ci.yml`에 4개 job으로 구현되어 있다.

### Backend job

- Python 3.12 + 의존성 설치(`requirements-dev.txt`)
- Postgres 서비스 컨테이너 기동
- 린트(`ruff check`)
- 테스트 실행(`pytest`)

### Frontend job

- Node 20 + 의존성 설치
- 린트(`eslint`), 타입 검사(`tsc --noEmit`)
- 테스트(`vitest`)
- 프로덕션 빌드

### Security job

- 의존성 취약점 검사: 백엔드 `pip-audit`, 프론트 `npm audit` (`continue-on-error`, 실제 실패 처리 전환은 E7-07에서 결정)
- 비밀값 유출 검사: `gitleaks`
- 업로드 보안 테스트는 E3 구현 후 backend job에 추가한다.

### Docker job

- `docker compose config`로 설정 검증
- backend/frontend 이미지 빌드

### 코드 자체 취약점 스캔과 의존성 알림

- `.github/workflows/codeql.yml`: push/PR과 매주 월요일에 backend(Python)와 frontend(TypeScript) 코드를 CodeQL로 스캔한다.
- `.github/dependabot.yml`: pip, npm, Docker 베이스 이미지, GitHub Actions 의존성을 매주 점검하고 업데이트 PR을 만든다.

위 4개 job과 CodeQL, Dependabot은 이미 도입되어 있다. 처음 계획했던 단계적 도입(1단계 test/build → 2단계 lint → 3단계 audit/secret → 4단계 Docker)은 한 번에 반영했다.

## 6. CD 기준

현재 배포 대상이 정해져 있지 않으므로 처음에는 CI까지만 구현한다.

배포 환경이 정해지면 다음 흐름을 사용한다.

```text
main 병합
→ CI 통과
→ Docker 이미지 빌드
→ 이미지 저장소 업로드
→ 스테이징 배포
→ smoke test
→ 수동 승인
→ 운영 배포
```

교육 프로젝트의 초기 배포는 Docker Compose 기반 단일 서버 또는 스테이징 환경으로 제한한다. 운영 배포 자동화는 실제 호스팅 위치, 도메인, 데이터베이스 백업, 비밀값 관리 방식이 정해진 뒤 추가한다.

## 7. 요구사항 검증 방식

모든 요구사항은 아래 연결을 가져야 한다.

```text
요구사항 번호
→ 에픽과 작업 번호
→ 구현 파일
→ 테스트 코드
→ 화면·API·로그 증거
```

### 에픽 시작 전 작업

각 에픽을 시작하기 전에 다음 순서로 해당 에픽의 작업을 상세화한다.

1. 원본 요구사항과 `requirements-matrix.md`의 매핑을 다시 확인한다.
2. 작업별 결정 필요 항목을 확인하고 관련 ADR이 없으면 ADR을 먼저 작성한다.
3. 작업별 완료 조건을 검증 가능한 문장으로 작성한다.
4. 허용 시나리오와 거부 시나리오를 포함한 테스트 종류와 경로를 정한다.
5. API 응답, 테스트 로그, 화면 캡처 등 완료 증거를 정한다.
6. 상세화한 작업을 구현하고 완료한 뒤 검증표의 상태와 증거를 갱신한다.

에픽을 시작하기 전에는 번호와 요구사항 매핑만 미리 정한다. 실제 완료 조건과 테스트 세부사항은 앞선 에픽의 구현 결과에 영향을 받을 수 있으므로 해당 에픽 착수 시 확정한다.

예시:

```text
SEC-005
→ E2-03
→ projects.py, analyses.py, findings.py
→ test_project_access.py
→ 권한 없는 프로젝트 조회가 차단된 API 응답
```

## 8. 저장소 운영 문서

저장소에는 다음 문서를 유지한다.

- `README.md`: 프로젝트 소개, 실행 방법, 기본 계정과 데모 흐름
- `DESIGN.md`: UI와 UX 결정 기준
- 별도 보관 중인 원본 요구사항 DOCX: 저장소에 커밋하지 않는 기준 문서
- `docs/epic/epic-sast-mvp.md`: 기능 에픽과 완료 조건
- `docs/requirements-interpretation.md`: 요구사항 해석, 가정, 멘토 질문과 답변
- `docs/implementation-strategy.md`: 기술 선택과 MVP 구현 전략
- `docs/development-workflow.md`: 브랜치, 커밋, PR, CI/CD 규칙
- `docs/requirements-matrix.md`: 요구사항과 테스트·증거 연결표
- `docs/api-contract.md`: 프론트와 백엔드가 공유하는 API 계약 초안
- `docs/adr/`: 설계 결정 기록
- `docs/troubleshooting/`: 해결된 문제와 재현 방법 기록
- `docs/templates/troubleshooting.md`: 트러블슈팅 기록 양식

## 9. AI 역할 분담

### Codex

- 구현, 테스트 작성, 테스트 실행, CI 실패 수정
- 저장소 분석과 요구사항 검증 증거 수집
- 트러블슈팅 기록 작성

### Claude

- UI·UX 설계 검토
- PR 코드 리뷰
- 보안·회귀·요구사항 누락 검토
- 트러블슈팅 기록의 재현성 검토

PR 코드 리뷰는 GitHub Actions로 자동 실행되지 않는다. PR을 만든 뒤 사람이 Claude Code에서 `/code-review <PR 번호 또는 브랜치>`를 직접 요청해야 리뷰가 실행된다.

어떤 PR에 리뷰가 필요한지를 매번 판단하지 않아도 되도록, 기본값은 "리뷰한다"이고 아래 목록만 예외로 생략한다.

**리뷰 생략 가능** (아래에 전부 해당할 때만):

- 문서(`docs/`, `README.md`, `*.md`) 텍스트 수정, 오탈자 수정
- 프론트 카피/스타일(색상, 여백 등)만 바뀌고 로직·API 호출이 그대로인 변경
- CI 설정처럼 동작 로직이 아닌 파일 변경

**나머지는 전부 리뷰한다.** 특히 아래는 절대 생략하지 않는다.

- `backend/app/core/`, 인증·권한 관련 라우터 코드
- 파일 업로드/경로 처리 코드 (E3)
- Alembic 마이그레이션, 모델 필드 변경
- API 응답 스키마 변경(`docs/api-contract.md`에 없는 필드 추가·제거 포함)
- SEC-*, DAR-* 요구사항과 연결된 작업
- ADR로 이미 결정된 내용과 다르게 구현된 부분

판단이 애매하면 생략하지 말고 리뷰를 요청한다.

### 공통 순서

```text
Codex 구현
→ Codex 1차 검증
→ Claude 리뷰 (/code-review 수동 요청)
→ Codex 수정
→ Codex 회귀 검증
→ 사람 승인
```

모든 트러블슈팅은 `docs/templates/troubleshooting.md`를 복사해 `docs/troubleshooting/`에 저장한다.

## 10. 현재 바로 할 일

1. Pen.dev에서 로그인과 전체 핵심 화면 흐름을 설계한다.
2. E0 디자인 결과를 `DESIGN.md`에 반영한다.
3. GitHub 저장소 이름과 공개 여부를 결정한다.
4. 로컬 Git 저장소를 초기화하고 첫 커밋을 만든다.
5. `main` 보호와 GitHub Actions CI를 설정한다.
6. E1 데이터 모델과 API 계약을 확정한다.

실제 탐지 항목 수와 분석 엔진은 E4 전에 결정하며, 원본 요구사항에 없는 특정 개수를 미리 확정하지 않는다. 소스 등록 범위, 조치 권고 보존, 비인가 응답, 역할별 응답 스키마는 각각 ADR-006부터 ADR-009에서 결정한다.
