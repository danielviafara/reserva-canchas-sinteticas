"""Carga de datos de prueba si la base esta vacia."""
from datetime import time

from app.db.session import SessionLocal
from app.db import models
from app.core.security import hash_password


def seed():
    db = SessionLocal()
    try:
        if db.query(models.Cancha).count() == 0:
            db.add_all([
                models.Cancha(Nombre="Cancha 1", Superficie="Cesped sintetico"),
                models.Cancha(Nombre="Cancha 2", Superficie="Cesped sintetico"),
                models.Cancha(Nombre="Cancha 3", Superficie="Cesped sintetico"),
            ])
        if db.query(models.Franja).count() == 0:
            db.add_all([
                models.Franja(HoraInicio=time(18, 0), HoraFin=time(19, 0)),
                models.Franja(HoraInicio=time(19, 0), HoraFin=time(20, 0)),
                models.Franja(HoraInicio=time(20, 0), HoraFin=time(21, 0)),
                models.Franja(HoraInicio=time(21, 0), HoraFin=time(22, 0)),
            ])
        if db.query(models.Usuario).count() == 0:
            db.add_all([
                models.Usuario(Nombre="Administrador", Email="admin@goltime.com",
                               PasswordHash=hash_password("admin123"), Rol="admin"),
                models.Usuario(Nombre="Daniel Viafara", Email="daniel@correo.com",
                               PasswordHash=hash_password("cliente123"), Rol="cliente"),
            ])
        db.commit()
    finally:
        db.close()
