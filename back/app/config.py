from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    app_name: str = "SIVIGILA Moderno"
    env: str = "development"
    database_url: str = "postgresql+asyncpg://sivigila:sivigila@localhost:5432/sivigila"
    secret_key: str = "change-me-in-production"
    sql_echo: bool = False

    admin_username: str = "admin"
    admin_password: str = "Admin123!"
    admin_nombre: str = "Administrador SIVIGILA"


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
