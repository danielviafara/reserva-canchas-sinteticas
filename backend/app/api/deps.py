"""Dependencias: sesion de base de datos y usuario autenticado."""
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from app.db.session import SessionLocal
from app.core.security import leer_token

bearer = HTTPBearer(auto_error=False)


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(cred: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if cred is None:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Falta el token de sesion")
    datos = leer_token(cred.credentials)
    if not datos:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Token invalido o expirado")
    return {"usuario_id": int(datos["sub"]), "rol": datos.get("rol")}
