"""Punto de entrada de la API (Fase 2: estructura inicial del backend)."""
from fastapi import FastAPI

from app.api.routes import health

app = FastAPI(title="Sistema de Reserva de Canchas Sinteticas")
app.include_router(health.router)


@app.get("/")
def root():
    return {"mensaje": "API del sistema de reserva de canchas - Fase 2"}
