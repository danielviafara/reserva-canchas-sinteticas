"""Esquemas para las operaciones de administracion."""
from datetime import time
from typing import Optional
from pydantic import BaseModel, Field


class CanchaIn(BaseModel):
    nombre: str = Field(min_length=2, max_length=100)
    superficie: Optional[str] = Field(default=None, max_length=50)


class FranjaIn(BaseModel):
    hora_inicio: time
    hora_fin: time
