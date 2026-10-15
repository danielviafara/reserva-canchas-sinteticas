"""GolTime - API del sistema de reserva de canchas sinteticas."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.db.session import Base, engine
from app.db import models  # noqa: F401 (registra los modelos)
from app.db.seed import seed
from app.api.routes import auth, canchas, disponibilidad, reservas

app = FastAPI(title="GolTime - API de reservas")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_methods=["*"], allow_headers=["*"],
)


@app.on_event("startup")
def startup():
    Base.metadata.create_all(bind=engine)
    seed()


@app.get("/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(canchas.router)
app.include_router(disponibilidad.router)
app.include_router(reservas.router)
