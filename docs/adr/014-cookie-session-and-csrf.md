# ADR-014: 쿠키 기반 인증 세션과 CSRF 방어

## Context

초기 로그인 구현은 JWT를 응답 본문으로 반환하고 프론트엔드가 `localStorage`에 저장한다. 이 방식은 구현이 단순하지만, 같은 출처에서 실행되는 악성 JavaScript가 토큰을 읽어 외부로 전송할 수 있다. SecScan은 관리자 기능과 분석 대상 소스를 다루므로 브라우저에서 인증 토큰 값을 읽지 못하게 해야 한다.

쿠키 인증으로 바꾸면 브라우저가 인증 쿠키를 자동 전송하므로, 프로젝트 생성과 접근권한 변경 같은 쓰기 요청에는 CSRF 방어도 필요하다.

## Decision

- 로그인 성공 시 JWT는 응답 본문이나 브라우저 저장소가 아닌 `HttpOnly` 세션 쿠키로만 전달한다.
- 운영 환경의 세션 쿠키는 `Secure`, `HttpOnly`, `SameSite=Strict`, `Path=/` 속성을 사용한다. 로컬 개발과 테스트에서만 HTTPS가 없으므로 `Secure` 속성을 명시적 환경 설정으로 끌 수 있다.
- 세션의 절대 만료 시간은 로그인 시점부터 24시간이다. MVP에서는 유휴 시간 만료와 토큰 갱신을 구현하지 않는다.
- 로그인 시 서버가 별도 CSRF 값을 발급한다. 프론트엔드는 프로젝트 생성, 수정, 접근권한 부여와 해제처럼 서버 데이터를 바꾸는 요청에 `X-CSRF-Token` 헤더를 보낸다. 서버는 헤더와 서버가 발급한 CSRF 값을 검증한다.
- `GET /auth/me`는 인증 쿠키를 검증한 뒤 이메일과 역할만 반환한다. 프론트는 앱 시작과 새로고침 때 이 API로 현재 역할을 확인한다.
- `POST /auth/logout`은 세션 및 CSRF 쿠키를 만료시킨다. 모든 기기에서 발급 토큰을 강제로 폐기하는 기능은 MVP 범위에서 제외한다.

## Considered alternatives

- JWT를 `localStorage`에 유지한다. 구현은 빠르지만 XSS가 발생하면 인증 토큰을 읽을 수 있다.
- JWT를 `sessionStorage`에 저장한다. 탭을 닫으면 사라지지만 XSS로 읽을 수 있다는 문제는 남는다.
- 서버 세션 저장소와 토큰 폐기 목록을 운영한다. 다른 기기 강제 로그아웃까지 지원할 수 있지만, 현재 MVP에 필요한 데이터 모델과 운영 범위를 넘는다.

## Consequences

- 프론트는 토큰 값을 저장하거나 Authorization 헤더를 구성하지 않는다.
- 로그인 응답에는 인증 토큰, 비밀번호, 비밀번호 해시, 활성 상태를 포함하지 않는다.
- 인증 쿠키가 만료되거나 유효하지 않으면 프론트는 일반적인 로그인 안내만 보여주고 로그인 화면으로 이동한다.
- 프로젝트별 접근권한은 토큰 만료와 별개로 모든 요청에서 DB 관계를 다시 확인한다. 권한 해제는 즉시 적용된다.
- CSRF 토큰 검증과 쿠키 속성 검증은 E2 인증 테스트에 포함한다.

## References

- [OWASP HTML5 Security Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html)
- [OWASP Session Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Session_Management_Cheat_Sheet.html)
