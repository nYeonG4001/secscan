from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SESSION_EXPIRE_MINUTES: int = 60 * 24
    SESSION_COOKIE_NAME: str = "secscan_session"
    CSRF_COOKIE_NAME: str = "secscan_csrf"
    SESSION_COOKIE_SECURE: bool = True
    STORAGE_ROOT: str = "/var/lib/secscan/storage"
    STALE_WORKSPACE_RETENTION_HOURS: int = 24
    SEMGREP_CLI_PATH: str = "semgrep"
    SEMGREP_CLI_VERSION: str = "1.95.0"
    SEMGREP_TIMEOUT_SECONDS: int = 120
    SEMGREP_CPU_LIMIT_SECONDS: int = 120
    SEMGREP_ADDRESS_SPACE_LIMIT_BYTES: int = 1024 * 1024 * 1024

    model_config = {"env_file": ".env"}

    @property
    def session_max_age_seconds(self) -> int:
        return self.SESSION_EXPIRE_MINUTES * 60


settings = Settings()
