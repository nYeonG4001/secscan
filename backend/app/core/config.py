from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    SESSION_EXPIRE_MINUTES: int = 60 * 24
    SESSION_COOKIE_NAME: str = "secscan_session"
    CSRF_COOKIE_NAME: str = "secscan_csrf"
    SESSION_COOKIE_SECURE: bool = True

    model_config = {"env_file": ".env"}

    @property
    def session_max_age_seconds(self) -> int:
        return self.SESSION_EXPIRE_MINUTES * 60


settings = Settings()
