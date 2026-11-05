"""Conexion a la base de datos con SQLAlchemy (PostgreSQL; SQLite como respaldo)."""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

connect_args = {}
if settings.DATABASE_URL.startswith("sqlite"):
    connect_args = {"check_same_thread": False}

# echo controlado por configuracion: con SQL_ECHO=true se imprime en consola
# cada sentencia SQL (BEGIN/SELECT/INSERT/COMMIT/ROLLBACK), util para evidenciar
# las transacciones durante una demostracion. Por defecto va desactivado.
engine = create_engine(
    settings.DATABASE_URL,
    pool_pre_ping=True,
    connect_args=connect_args,
    echo=settings.SQL_ECHO,
)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
Base = declarative_base()
