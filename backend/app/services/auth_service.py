"""Logica de registro e inicio de sesion."""
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.db import models
from app.core.security import hash_password, verify_password, crear_token
from app.schemas.usuario import RegistroIn, LoginIn


def registrar(db: Session, datos: RegistroIn):
    if db.query(models.Usuario).filter(models.Usuario.Email == datos.email).first():
        raise HTTPException(status.HTTP_409_CONFLICT, "El correo ya esta registrado")
    u = models.Usuario(Nombre=datos.nombre, Email=datos.email,
                       PasswordHash=hash_password(datos.password), Rol="cliente")
    db.add(u)
    db.commit()
    db.refresh(u)
    return u


def login(db: Session, datos: LoginIn):
    u = db.query(models.Usuario).filter(models.Usuario.Email == datos.email).first()
    if not u or not verify_password(datos.password, u.PasswordHash):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Credenciales invalidas")
    return u, crear_token(u.UsuarioId, u.Rol)
