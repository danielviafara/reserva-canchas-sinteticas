"""Modelos ORM. Corresponden 1:1 con las tablas del modelo relacional (Fase 2)."""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Date, DateTime, Boolean, Time,
    ForeignKey, func,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Usuario(Base):
    __tablename__ = "Usuario"
    UsuarioId = Column(Integer, primary_key=True)
    Nombre = Column(String(120), nullable=False)
    Email = Column(String(256), nullable=False, unique=True)
    PasswordHash = Column(String(200), nullable=False)
    Rol = Column(String(20), nullable=False)          # 'cliente' | 'admin'
    Activo = Column(Boolean, nullable=False, default=True)
    CreadoEn = Column(DateTime, server_default=func.sysutcdatetime())

    reservas = relationship("Reserva", back_populates="usuario")


class Cancha(Base):
    __tablename__ = "Cancha"
    CanchaId = Column(Integer, primary_key=True)
    Nombre = Column(String(100), nullable=False, unique=True)
    Superficie = Column(String(50))
    Activa = Column(Boolean, nullable=False, default=True)

    reservas = relationship("Reserva", back_populates="cancha")


class Franja(Base):
    __tablename__ = "Franja"
    FranjaId = Column(Integer, primary_key=True)
    HoraInicio = Column(Time, nullable=False)
    HoraFin = Column(Time, nullable=False)
    Activa = Column(Boolean, nullable=False, default=True)

    reservas = relationship("Reserva", back_populates="franja")


class Reserva(Base):
    __tablename__ = "Reserva"
    ReservaId = Column(BigInteger, primary_key=True)
    CanchaId = Column(Integer, ForeignKey("Cancha.CanchaId"), nullable=False)
    FranjaId = Column(Integer, ForeignKey("Franja.FranjaId"), nullable=False)
    Fecha = Column(Date, nullable=False)
    UsuarioId = Column(Integer, ForeignKey("Usuario.UsuarioId"), nullable=False)
    Estado = Column(String(20), nullable=False)       # 'confirmada' | 'cancelada'
    CreadaEn = Column(DateTime, server_default=func.sysutcdatetime())
    CanceladaEn = Column(DateTime)

    cancha = relationship("Cancha", back_populates="reservas")
    franja = relationship("Franja", back_populates="reservas")
    usuario = relationship("Usuario", back_populates="reservas")
