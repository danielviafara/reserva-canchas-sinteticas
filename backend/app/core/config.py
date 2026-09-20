"""Configuracion del proyecto (se lee desde variables de entorno / .env)."""
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str = (
        "mssql+pyodbc://sa:TuPassword_123@localhost:1433/ReservaCanchas"
        "?driver=ODBC+Driver+18+for+SQL+Server&TrustServerCertificate=yes"
    )
    JWT_SECRET: str = "cambia-esta-clave"
    JWT_ALGORITHM: str = "HS256"


settings = Settings()
