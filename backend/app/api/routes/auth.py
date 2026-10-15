from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.deps import get_db
from app.schemas.usuario import RegistroIn, LoginIn, TokenOut, UsuarioOut
from app.services import auth_service

router = APIRouter(prefix="/auth", tags=["auth"])


def _usuario_out(u):
    return UsuarioOut(usuario_id=u.UsuarioId, nombre=u.Nombre, email=u.Email, rol=u.Rol)


@router.post("/register", response_model=TokenOut, status_code=status.HTTP_201_CREATED)
def register(datos: RegistroIn, db: Session = Depends(get_db)):
    u = auth_service.registrar(db, datos)
    _, token = auth_service.login(db, LoginIn(email=datos.email, password=datos.password))
    return TokenOut(access_token=token, usuario=_usuario_out(u))


@router.post("/login", response_model=TokenOut)
def login(datos: LoginIn, db: Session = Depends(get_db)):
    u, token = auth_service.login(db, datos)
    return TokenOut(access_token=token, usuario=_usuario_out(u))
