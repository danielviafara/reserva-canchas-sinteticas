"""Rutas del modulo de inteligencia artificial."""
from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import Response
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


@router.get("/ia/mi-perfil")
def mi_perfil(db: Session = Depends(get_db), user=Depends(get_current_user)):
    """Patron de juego del cliente: segmento, habitos, historial y recomendaciones."""
    return ia_service.mi_perfil(db, user["usuario_id"])


@router.get("/admin/ia")
def tablero(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Tablero de IA: demanda, pronostico, riesgo de cancelacion y segmentos."""
    return ia_service.resumen_admin(db)


@router.get("/admin/ia/clientes")
def clientes(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return ia_service.clientes(db)


@router.get("/admin/ia/clientes/{usuario_id}")
def cliente(usuario_id: int, db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    p = ia_service.perfil_cliente(db, usuario_id)
    if p is None:
        raise HTTPException(404, "Cliente no encontrado")
    return p


@router.get("/admin/ia/dataset")
def dataset(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    """Resumen del dataset con el que se entrena la IA (diccionario, distribuciones y muestra)."""
    return ia_service.dataset_resumen(db)


@router.get("/admin/ia/dataset.csv")
def dataset_csv(db: Session = Depends(get_db), admin=Depends(get_current_admin)):
    return Response(ia_service.dataset_csv(db), media_type="text/csv; charset=utf-8",
                    headers={"Content-Disposition": 'attachment; filename="goltime_dataset.csv"'})
