from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.schemas.reserva import ReservaIn
from app.services import reserva_service

router = APIRouter(prefix="/reservas", tags=["reservas"])


@router.get("")
def mis_reservas(db: Session = Depends(get_db), user=Depends(get_current_user)):
    from app.repositories import reserva_repo
    return [reserva_service.serializar(db, r)
            for r in reserva_repo.reservas_de_usuario(db, user["usuario_id"])]


@router.post("", status_code=status.HTTP_201_CREATED)
def reservar(datos: ReservaIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = reserva_service.crear_reserva(db, user["usuario_id"], datos.cancha_id,
                                      datos.franja_id, datos.fecha)
    return reserva_service.serializar(db, r)


@router.post("/{reserva_id}/cancelar")
def cancelar(reserva_id: int, db: Session = Depends(get_db), user=Depends(get_current_user)):
    r = reserva_service.cancelar_reserva(db, user["usuario_id"], reserva_id)
    return reserva_service.serializar(db, r)
