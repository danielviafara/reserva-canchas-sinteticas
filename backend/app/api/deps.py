"""Dependencias compartidas de la API."""
from app.db.session import SessionLocal


def get_db():
    """Entrega una sesion de base de datos y la cierra al terminar."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
