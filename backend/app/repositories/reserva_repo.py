"""Acceso a datos para reservas, canchas y franjas."""
from datetime import date

from sqlalchemy.orm import Session

from app.db import models


def listar_canchas(db: Session):
    return db.query(models.Cancha).filter(models.Cancha.Activa == True).all()


def listar_franjas(db: Session):
    return db.query(models.Franja).filter(models.Franja.Activa == True)\
        .order_by(models.Franja.HoraInicio).all()


def franjas_ocupadas(db: Session, cancha_id: int, fecha: date):
    filas = db.query(models.Reserva.FranjaId).filter(
        models.Reserva.CanchaId == cancha_id,
        models.Reserva.Fecha == fecha,
        models.Reserva.Estado == "confirmada",
    ).all()
    return {f[0] for f in filas}


def existe_confirmada(db: Session, cancha_id: int, franja_id: int, fecha: date) -> bool:
    return db.query(models.Reserva.ReservaId).filter(
        models.Reserva.CanchaId == cancha_id,
        models.Reserva.FranjaId == franja_id,
        models.Reserva.Fecha == fecha,
        models.Reserva.Estado == "confirmada",
    ).first() is not None


def reservas_de_usuario(db: Session, usuario_id: int):
    return db.query(models.Reserva).filter(models.Reserva.UsuarioId == usuario_id)\
        .order_by(models.Reserva.CreadaEn.desc()).all()
