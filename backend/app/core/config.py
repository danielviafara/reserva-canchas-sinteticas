"""Configuracion leida desde variables de entorno o .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # SQLite por defecto para ejecucion inmediata; SQL Server en produccion.
    DATABASE_URL: str = "sqlite:///./goltime.db"
    JWT_SECRET: str = "cambia-esta-clave-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720


settings = Settings()
