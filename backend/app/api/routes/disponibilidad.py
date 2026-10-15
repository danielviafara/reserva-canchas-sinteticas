from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.services import reserva_service

router = APIRouter(prefix="/disponibilidad", tags=["disponibilidad"])


@router.get("")
def disponibilidad(cancha_id: int = Query(gt=0), fecha: date = Query(...),
                   db: Session = Depends(get_db)):
    return reserva_service.consultar_disponibilidad(db, cancha_id, fecha)
