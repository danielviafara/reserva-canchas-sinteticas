"""Esquemas de validacion para disponibilidad y reservas."""
from datetime import date
from pydantic import BaseModel, Field, EmailStr


class ReservaIn(BaseModel):
    cancha_id: int = Field(gt=0)
    franja_id: int = Field(gt=0)
    fecha: date
    nombre_contacto: str = Field(min_length=3, max_length=120)
    celular: str = Field(min_length=7, max_length=30)
    correo_contacto: EmailStr


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
