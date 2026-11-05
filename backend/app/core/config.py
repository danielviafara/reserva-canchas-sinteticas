"""Configuracion leida desde variables de entorno o .env."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")
    # PostgreSQL en el prototipo; SQLite queda como respaldo para una prueba rapida.
    DATABASE_URL: str = "sqlite:///./goltime.db"
    JWT_SECRET: str = "cambia-esta-clave-en-produccion"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 720
    # SQL_ECHO=true imprime en consola cada sentencia SQL (evidencia de transacciones).
    SQL_ECHO: bool = False


settings = Settings()
