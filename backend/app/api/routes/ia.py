"""Rutas del modulo de inteligencia artificial."""
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user, get_current_admin
from app.services import ia_service

router = APIRouter(tags=["ia"])


@router.get("/ia/demanda")
def demanda(cancha_id: int = Query(gt=0), fecha: date = Query(...), db: Session = Depends(get_db)):
    """Probabilidad estimada de ocupacion de cada franja (para etiquetar la disponibilidad)."""
    return ia_service.demanda_dia(db, cancha_id, fecha)


@router.get("/ia/recomendaciones")
def recomendaciones(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Franjas libres sugeridas segun los habitos del cliente."""
    return ia_service.recomendaciones(db, user["usuario_id"])


@router.get("/admin/ia")
def tablero(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Tablero de IA: demanda, pronostico, riesgo de cancelacion y segmentos."""
    return ia_service.resumen_admin(db)
