#!/usr/bin/env python3
"""시드 스크립트: admin / user 계정 생성"""
import os
import sys

# Allow running from project root inside Docker
sys.path.insert(0, os.path.dirname(__file__))

from app.core.database import SessionLocal
from app.core.security import hash_password
from app.models.user import User
from app.services.kisa_catalog_seed import seed_kisa_catalog


def seed():
    db = SessionLocal()
    try:
        required = {
            "ADMIN_SEED_EMAIL": os.getenv("ADMIN_SEED_EMAIL"),
            "ADMIN_SEED_PASSWORD": os.getenv("ADMIN_SEED_PASSWORD"),
            "USER_SEED_EMAIL": os.getenv("USER_SEED_EMAIL"),
            "USER_SEED_PASSWORD": os.getenv("USER_SEED_PASSWORD"),
        }
        missing = [name for name, value in required.items() if not value]
        if missing:
            raise RuntimeError(
                "시드 계정 환경 변수가 없습니다: " + ", ".join(missing)
            )

        seeds = [
            {
                "email": required["ADMIN_SEED_EMAIL"],
                "password": required["ADMIN_SEED_PASSWORD"],
                "role": "ADMIN",
            },
            {
                "email": required["USER_SEED_EMAIL"],
                "password": required["USER_SEED_PASSWORD"],
                "role": "USER",
            },
        ]
        for s in seeds:
            existing = db.query(User).filter(User.email == s["email"]).first()
            if existing:
                print(f"  이미 존재: {s['email']}")
            else:
                user = User(
                    email=s["email"],
                    password_hash=hash_password(s["password"]),
                    role=s["role"],
                )
                db.add(user)
                print(f"  생성: {s['email']} ({s['role']})")
        db.commit()

        inserted = seed_kisa_catalog(db)
        print(f"  KISA 카탈로그: {inserted}개 신규 등록 (총 49개 기준)")

        print("Seed 완료")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
