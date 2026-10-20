"""Modelos ORM. Corresponden al modelo relacional del documento maestro."""
from sqlalchemy import (
    Column, Integer, BigInteger, String, Date, DateTime, Boolean, Time,
    ForeignKey, Index, func, text,
)
from sqlalchemy.orm import relationship

from app.db.session import Base


class Usuario(Base):
    __tablename__ = "Usuario"
    UsuarioId = Column(Integer, primary_key=True)
    Nombre = Column(String(120), nullable=False)
    Email = Column(String(256), nullable=False, unique=True)
    PasswordHash = Column(String(200), nullable=False)
    Rol = Column(String(20), nullable=False, default="cliente")  # cliente | admin
    Activo = Column(Boolean, nullable=False, default=True)
    CreadoEn = Column(DateTime, server_default=func.now())
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
    ReservaId = Column(BigInteger().with_variant(Integer, "sqlite"), primary_key=True)
    CanchaId = Column(Integer, ForeignKey("Cancha.CanchaId"), nullable=False)
    FranjaId = Column(Integer, ForeignKey("Franja.FranjaId"), nullable=False)
    Fecha = Column(Date, nullable=False)
    UsuarioId = Column(Integer, ForeignKey("Usuario.UsuarioId"), nullable=False)
    Estado = Column(String(20), nullable=False, default="confirmada")  # confirmada | cancelada
    CreadaEn = Column(DateTime, server_default=func.now())
    CanceladaEn = Column(DateTime)
    cancha = relationship("Cancha", back_populates="reservas")
    franja = relationship("Franja", back_populates="reservas")
    usuario = relationship("Usuario", back_populates="reservas")


# INVARIANTE DEL SISTEMA: una sola reserva 'confirmada' por (cancha, fecha, franja).
# Indice unico filtrado; funciona en SQLite (sqlite_where) y SQL Server (mssql_where).
Index(
    "UX_Reserva_Slot_Confirmada",
    Reserva.CanchaId, Reserva.Fecha, Reserva.FranjaId,
    unique=True,
    sqlite_where=text("Estado = 'confirmada'"),
    mssql_where=text("Estado = 'confirmada'"),
    postgresql_where=text("\"Estado\" = 'confirmada'"),
)
