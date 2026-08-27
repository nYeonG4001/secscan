# Troubleshooting: EmailStr가 .local 도메인을 거부하고, 마이그레이션 테스트가 alembic_version 부기와 어긋남

## 기본 정보

- 작성일: 2026-08-27
- 작성자: Claude (Codex 토큰 소진으로 대신 진행)
- 관련 에픽: E1-01
- 관련 요구사항: SFR-001, SFR-002, DAR-001, DAR-002
- 관련 PR 또는 커밋: 없음 (커밋 전)
- 환경: 로컬 (Docker Postgres, Python 3.12 venv)

## 문제 요약

Docker와 Python 3.12 환경을 준비해 E1-01을 실제로 검증하는 과정에서 서로 다른 원인의 버그 2건을 발견했다. 하나는 로그인 관련 테스트 전부가 422로 실패했고, 다른 하나는 새로 작성한 마이그레이션 테스트 4건이 전부 실패했다.

## 증상

```text
# 1) 로그인 테스트 전부 실패
assert response.status_code == 200
E   assert 422 == 200

{'detail': [{'type': 'value_error', 'loc': ['body', 'email'],
  'msg': "value is not a valid email address: The part after the @-sign is a
  special-use or reserved name that cannot be used with email.", ...}]}

# 2) 마이그레이션 테스트 전부 실패 (두 번째 테스트부터)
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable)
relation "users" does not exist
[SQL: ALTER TABLE users DROP CONSTRAINT ck_users_role]
```

## 재현 방법

1. `backend`에서 Python 3.12 venv에 `requirements-dev.txt`를 설치한다.
2. Docker로 전용 Postgres 테스트 DB(`secscan_test`)를 띄운다.
3. `TEST_DATABASE_URL`을 설정하고 `pytest -q`를 실행한다.

## 기대 결과

`admin@secscan.local` 같은 시드 계정으로 로그인이 성공하고, `test_migrations.py`가 0001→0002 업그레이드·다운그레이드를 반복 검증해도 매번 통과해야 한다.

## 실제 결과

- 로그인 테스트 15개 전원이 422로 실패했다.
- 새로 작성한 마이그레이션 테스트 중 첫 번째만 통과하고 나머지 3개가 실패했다.

## 원인 분석

- 확인한 증거:
  - `email_validator/syntax.py`의 `SPECIAL_USE_DOMAIN_NAMES`에 `local`이 IANA 특수 예약 도메인(mDNS, RFC 6762)으로 등록되어 있어, Pydantic의 `EmailStr`이 이 라이브러리를 그대로 호출하면 `.local` 도메인의 이메일을 문법 오류로 거부한다. `test_environment=True` 옵션도 `test` 도메인 하나만 예외 처리할 뿐 `local`에는 적용되지 않는다.
  - `backend/tests/test_migrations.py`의 `alembic_config` fixture가 `Base.metadata.drop_all(bind=engine)`만 호출했다. 이 함수는 SQLAlchemy ORM이 아는 테이블만 지우고, Alembic이 자체 관리하는 `alembic_version` 부기 테이블은 지우지 않는다. 그 결과 두 번째 테스트부터 `alembic_version`이 이전 테스트가 남긴 `0002`(head) 상태를 그대로 가리켰고, `command.upgrade(config, "head")`가 "이미 head"로 판단해 실제로는 방금 지워진 테이블을 재생성하지 않은 채 아무 일도 하지 않았다. 이어지는 `downgrade("0001")`이 존재하지 않는 `users` 테이블에 `ALTER TABLE`을 시도해 실패했다.
- 원인: (1) `.local` 도메인과 `EmailStr`의 충돌, (2) 마이그레이션 테스트 fixture가 ORM 메타데이터와 Alembic 부기 테이블을 따로 관리하지 않은 것.
- 원인이 아니었던 가설: E1-01의 `active`/`created_at`/`updated_at` 컬럼 추가 로직이나 0002 마이그레이션 SQL 자체의 오류. 실제로는 두 마이그레이션 스크립트 모두 정상 작동했다.

## 해결 방법

- 변경 파일:
  - `.env.example`, `.github/workflows/ci.yml`, `docs/api-contract.md`, `backend/tests/test_auth_api.py`, `backend/tests/test_user_model.py`
  - `backend/tests/test_migrations.py`
- 변경 내용:
  - 데모/테스트 계정 도메인을 `secscan.local`에서 `secscan.io`로 전환했다(예약되지 않은 도메인이라 `EmailStr` 검증을 통과한다). 사용자에게 확인 후 진행했다.
  - `alembic_config` fixture에 `DROP TABLE IF EXISTS alembic_version`을 추가해, 매 테스트 시작 전 ORM 테이블과 Alembic 부기 테이블을 함께 초기화하도록 고쳤다.

## 검증

- [x] 같은 재현 절차로 문제가 해결됨
- [x] 관련 단위 테스트 통과
- [x] 관련 통합 또는 화면 테스트 통과
- [x] 기존 기능 회귀 없음
- [x] 보안 영향 확인 (도메인 전환은 검증 로직과 무관, 데모 계정 값 교체일 뿐)

```text
cd backend && export TEST_DATABASE_URL=postgresql://secscan:secscan@localhost:5433/secscan_test SECRET_KEY=test-secret-key
.venv/bin/ruff check .        → All checks passed!
.venv/bin/python -m pytest -q → 19 passed (3회 연속 재실행해 격리 확인)
```

## 남은 위험과 후속 작업

- 남은 문제: 없음.
- 후속 작업: 팀/문서에 남아있는 다른 `.local` 참조가 있다면 `.io`로 통일이 필요한지 확인한다(README.md와 seed.py는 env var만 참조하므로 영향 없음을 확인함).
- 관련 문서 업데이트: `.env.example`, `docs/api-contract.md`

## 참고 자료

- 로그 경로: 현재 작업 세션의 pytest 출력
- 화면 캡처: 없음
- 관련 커밋: 없음 (이 기록과 함께 커밋 예정)
