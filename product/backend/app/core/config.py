from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "DevinciWatch API"
    app_env: str = "dev"

    secret_key: str = "change-me-in-production"
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 60

    database_url: str = "postgresql+psycopg://postgres:postgres@localhost:5432/devinciwatch"
    redis_url: str = "redis://localhost:6379/0"

    default_admin_username: str = "admin"
    default_admin_password: str = "ChangeMeNow123!"

    agent_ingest_key: str = "devinciwatch-agent-key-change-me"

    cors_allow_origins: str = "http://localhost:3000,http://127.0.0.1:3000"

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=False)

    @property
    def cors_origins(self) -> list[str]:
        raw = self.cors_allow_origins.strip()
        if raw == "*":
            return ["*"]
        return [o.strip() for o in raw.split(",") if o.strip()]


settings = Settings()
