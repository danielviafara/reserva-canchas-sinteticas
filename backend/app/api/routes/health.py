"""Rutas de verificacion (health check)."""
from fastapi import APIRouter, Depends
from sqlalchemy import text

from app.api.deps import get_db

router = APIRouter(tags=["health"])


@router.get("/health")
def health():
    return {"status": "ok"}


@router.get("/health/db")
def health_db(db=Depends(get_db)):
    """Comprueba que el backend se conecta a la base de datos."""
    db.execute(text("SELECT 1"))
    return {"database": "ok"}
