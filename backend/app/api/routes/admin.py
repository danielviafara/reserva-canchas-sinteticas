"""Rutas de administracion, protegidas por rol admin."""
from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_admin
from app.schemas.admin import CanchaIn, FranjaIn
from app.services import admin_service

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/reservas")
def reservas(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.listar_reservas(db)


@router.get("/canchas")
def canchas(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.listar_canchas(db)


@router.post("/canchas", status_code=status.HTTP_201_CREATED)
def crear_cancha(datos: CanchaIn, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.crear_cancha(db, datos)


@router.patch("/canchas/{cancha_id}/toggle")
def toggle_cancha(cancha_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.toggle_cancha(db, cancha_id)


@router.get("/franjas")
def franjas(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.listar_franjas(db)


@router.post("/franjas", status_code=status.HTTP_201_CREATED)
def crear_franja(datos: FranjaIn, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.crear_franja(db, datos)


@router.patch("/franjas/{franja_id}/toggle")
def toggle_franja(franja_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.toggle_franja(db, franja_id)


@router.post("/reservas/{reserva_id}/cancelar")
def cancelar_reserva(reserva_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return admin_service.cancelar_reserva(db, reserva_id)
