"""Esquemas de validacion para disponibilidad y reservas."""
from datetime import date
from pydantic import BaseModel, Field


class ReservaIn(BaseModel):
    cancha_id: int = Field(gt=0)
    franja_id: int = Field(gt=0)
    fecha: date


class FranjaDisponibilidad(BaseModel):
    franja_id: int
    hora_inicio: str
    hora_fin: str
    estado: str  # libre | ocupada


class ReservaOut(BaseModel):
    reserva_id: int
    cancha: str
    fecha: date
    hora_inicio: str
    hora_fin: str
    estado: str
