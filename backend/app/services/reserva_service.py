"""Logica de negocio: disponibilidad, reserva y cancelacion.

La operacion de reserva es el nucleo transaccional del sistema: comprueba que la
franja siga libre y la registra dentro de una transaccion. El indice unico
filtrado de la base de datos es el respaldo que vuelve imposible la doble reserva.
"""
from datetime import date, datetime

from fastapi import HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.db import models
from app.repositories import reserva_repo


def _hhmm(t) -> str:
    return t.strftime("%H:%M")


def consultar_disponibilidad(db: Session, cancha_id: int, fecha: date):
    cancha = db.get(models.Cancha, cancha_id)
    if not cancha:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cancha no existe")
    ocupadas = reserva_repo.franjas_ocupadas(db, cancha_id, fecha)
    salida = []
    for f in reserva_repo.listar_franjas(db):
        salida.append({
            "franja_id": f.FranjaId,
            "hora_inicio": _hhmm(f.HoraInicio),
            "hora_fin": _hhmm(f.HoraFin),
            "estado": "ocupada" if f.FranjaId in ocupadas else "libre",
        })
    return salida


def crear_reserva(db: Session, usuario_id: int, cancha_id: int, franja_id: int, fecha: date):
    if not db.get(models.Cancha, cancha_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La cancha no existe")
    if not db.get(models.Franja, franja_id):
        raise HTTPException(status.HTTP_404_NOT_FOUND, "La franja no existe")

    # Comprobacion dentro de la transaccion.
    if reserva_repo.existe_confirmada(db, cancha_id, franja_id, fecha):
        raise HTTPException(status.HTTP_409_CONFLICT, "La franja ya fue reservada")

    reserva = models.Reserva(CanchaId=cancha_id, FranjaId=franja_id, Fecha=fecha,
                             UsuarioId=usuario_id, Estado="confirmada")
    db.add(reserva)
    try:
        db.commit()
    except IntegrityError:
        # Respaldo: el indice unico filtrado evita la doble reserva en una carrera.
        db.rollback()
        raise HTTPException(status.HTTP_409_CONFLICT, "La franja ya fue reservada")
    db.refresh(reserva)
    return reserva


def cancelar_reserva(db: Session, usuario_id: int, reserva_id: int):
    reserva = db.get(models.Reserva, reserva_id)
    if not reserva or reserva.UsuarioId != usuario_id:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Reserva no encontrada")
    if reserva.Estado == "cancelada":
        raise HTTPException(status.HTTP_409_CONFLICT, "La reserva ya estaba cancelada")
    reserva.Estado = "cancelada"
    reserva.CanceladaEn = datetime.utcnow()
    db.commit()
    return reserva


def serializar(db: Session, r: models.Reserva) -> dict:
    return {
        "reserva_id": r.ReservaId,
        "cancha": r.cancha.Nombre,
        "fecha": r.Fecha,
        "hora_inicio": _hhmm(r.franja.HoraInicio),
        "hora_fin": _hhmm(r.franja.HoraFin),
        "estado": r.Estado,
    }
