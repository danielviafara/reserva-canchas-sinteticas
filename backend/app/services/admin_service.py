"""Logica de administracion: reservas globales, canchas y franjas."""
from datetime import datetime
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.db import models
from app.schemas.admin import CanchaIn, FranjaIn


def _hhmm(t):
    return t.strftime("%H:%M")


def listar_reservas(db: Session):
    reservas = (db.query(models.Reserva)
                .order_by(models.Reserva.Fecha.desc(), models.Reserva.ReservaId.desc())
                .all())
    return [{
        "reserva_id": r.ReservaId,
        "cancha": r.cancha.Nombre,
        "fecha": r.Fecha,
        "hora_inicio": _hhmm(r.franja.HoraInicio),
        "hora_fin": _hhmm(r.franja.HoraFin),
        "estado": r.Estado,
        "usuario": r.usuario.Nombre,
        "nombre_contacto": r.NombreContacto,
        "celular": r.Celular,
        "correo_contacto": r.CorreoContacto,
    } for r in reservas]


def _cancha_dict(c):
    return {"cancha_id": c.CanchaId, "nombre": c.Nombre,
            "superficie": c.Superficie, "activa": c.Activa}


def listar_canchas(db: Session):
    return [_cancha_dict(c) for c in db.query(models.Cancha).order_by(models.Cancha.CanchaId).all()]


def crear_cancha(db: Session, datos: CanchaIn):
    if db.query(models.Cancha).filter(models.Cancha.Nombre == datos.nombre).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe una cancha con ese nombre")
    c = models.Cancha(Nombre=datos.nombre, Superficie=datos.superficie)
    db.add(c); db.commit(); db.refresh(c)
    return _cancha_dict(c)


def toggle_cancha(db: Session, cancha_id: int):
    c = db.get(models.Cancha, cancha_id)
    if not c:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Cancha no encontrada")
    c.Activa = not c.Activa
    db.commit()
    return _cancha_dict(c)


def _franja_dict(f):
    return {"franja_id": f.FranjaId, "hora_inicio": _hhmm(f.HoraInicio),
            "hora_fin": _hhmm(f.HoraFin), "activa": f.Activa}


def listar_franjas(db: Session):
    return [_franja_dict(f) for f in db.query(models.Franja).order_by(models.Franja.HoraInicio).all()]


def crear_franja(db: Session, datos: FranjaIn):
    if datos.hora_fin <= datos.hora_inicio:
        raise HTTPException(status.HTTP_422_UNPROCESSABLE_ENTITY,
                            "La hora de fin debe ser mayor a la de inicio")
    existe = (db.query(models.Franja)
              .filter(models.Franja.HoraInicio == datos.hora_inicio,
                      models.Franja.HoraFin == datos.hora_fin).first())
    if existe:
        raise HTTPException(status.HTTP_409_CONFLICT, "Ya existe esa franja")
    f = models.Franja(HoraInicio=datos.hora_inicio, HoraFin=datos.hora_fin)
    db.add(f); db.commit(); db.refresh(f)
    return _franja_dict(f)


def toggle_franja(db: Session, franja_id: int):
    f = db.get(models.Franja, franja_id)
    if not f:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Franja no encontrada")
    f.Activa = not f.Activa
    db.commit()
    return _franja_dict(f)


def cancelar_reserva(db: Session, reserva_id: int):
    r = db.get(models.Reserva, reserva_id)
    if not r:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    if r.Estado == "cancelada":
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva ya estaba cancelada")
    r.Estado = "cancelada"
    r.CanceladaEn = datetime.utcnow()
    db.commit()
    return {"reserva_id": r.ReservaId, "estado": r.Estado}
