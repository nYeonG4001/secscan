import os

os.environ.setdefault("DATABASE_URL", "postgresql://secscan:secscan@localhost:5432/secscan_test")
os.environ.setdefault("SECRET_KEY", "test-secret-key")
