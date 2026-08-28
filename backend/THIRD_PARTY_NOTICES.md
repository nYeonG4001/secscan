# 외부 구성요소 고지

## Semgrep OSS CLI

- 구성요소: `semgrep` Python 패키지 1.95.0
- 출처: Semgrep, Inc.의 [Semgrep OSS 저장소](https://github.com/semgrep/semgrep), release `v1.95.0`
- 용도: SecScan 자체 작성 규칙의 정적 분석 실행 엔진
- 라이선스: GNU Lesser General Public License v2.1 (`LGPL-2.1`)
- 확인일: 2026-08-28

SecScan은 Semgrep 공식 규칙이나 다른 제3자 Semgrep 규칙을 포함하지 않는다. 실행 규칙은
`semgrep-rules/` 아래의 SecScan 자체 작성 규칙으로 한정한다.
