from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.repositories import reserva_repo

router = APIRouter(prefix="/canchas", tags=["canchas"])


@router.get("")
def listar(db: Session = Depends(get_db)):
    return [{"cancha_id": c.CanchaId, "nombre": c.Nombre, "superficie": c.Superficie}
            for c in reserva_repo.listar_canchas(db)]
