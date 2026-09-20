# Sistema de Reserva de Canchas Sintéticas

![Estado](https://img.shields.io/badge/estado-fase%202%20(BD%20%2B%20backend)-blue)

Aplicación para reservar canchas sintéticas por franjas horarias, pensada para
evitar que dos personas terminen con el mismo turno de la misma cancha.

> Proyecto académico — Universidad Manuela Beltrán · Arquitectura de Software · Quinto semestre.

---

## ¿Qué problema resuelve?

Hoy muchas canchas gestionan sus reservas por llamadas, mensajería o cuadernos.
Cuando dos personas piden la misma franja casi al mismo tiempo, es fácil que
ambas queden confirmadas y se produzca una **doble reserva**. Este sistema
centraliza la disponibilidad para que eso no pase.

## Objetivo

Construir una aplicación que permita consultar la disponibilidad, reservar y
cancelar turnos de forma confiable, garantizando que solo exista una reserva por
cancha, fecha y franja.

## ¿Qué podrá hacer el sistema?

- Registrar clientes, canchas y horarios
- Consultar la disponibilidad en tiempo real
- Reservar por franja horaria
- Cancelar una reserva y liberar el cupo
- Consultar el historial de reservas
- Generar reportes básicos de ocupación

## Tecnologías

- **Aplicación:** React + Vite
- **Servidor:** FastAPI (Python)
- **Base de datos:** SQL Server
- **Autenticación:** JWT
- **Despliegue:** Vercel (app) y Docker (servidor)

## Estructura del proyecto

```
reserva-canchas-sinteticas/
├─ README.md
├─ docs/            # documentación y propuesta visual
├─ database/        # scripts de la base de datos (SQL Server)
│  ├─ 01_create_database.sql
│  ├─ 02_tables.sql
│  └─ 03_seed.sql
└─ backend/         # servidor (FastAPI)
   ├─ app/
   │  ├─ api/          # rutas y dependencias
   │  ├─ core/         # configuración
   │  ├─ db/           # conexión y modelos
   │  ├─ schemas/      # (se completa más adelante)
   │  ├─ services/     # (se completa más adelante)
   │  └─ repositories/ # (se completa más adelante)
   ├─ requirements.txt
   ├─ .env.example
   └─ Dockerfile
```

## Cómo ejecutar

### 1. Base de datos

Requiere **SQL Server**. Ejecutar los scripts de `database/` en orden
(con `sqlcmd`, Azure Data Studio o SQL Server Management Studio):

```bash
sqlcmd -S localhost -U sa -P TuPassword_123 -i database/01_create_database.sql
sqlcmd -S localhost -U sa -P TuPassword_123 -i database/02_tables.sql
sqlcmd -S localhost -U sa -P TuPassword_123 -i database/03_seed.sql
```

Esto crea la base de datos `ReservaCanchas`, las tablas y algunos datos de prueba.

### 2. Backend

Requiere **Python 3.12** y el driver **ODBC Driver 18 for SQL Server**.

```bash
cd backend
cp .env.example .env           # ajusta la cadena de conexión
python -m venv .venv
source .venv/bin/activate       # Windows: .venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000`. Para probar la conexión con la base de
datos: `http://localhost:8000/health/db`.

## Estado del proyecto

- **Fase 1:** prototipo inicial y propuesta visual ✅
- **Fase 2:** base de datos + estructura inicial del backend ✅
- **Siguiente:** operaciones transaccionales (disponibilidad, reserva, cancelación)

## Autor

**Daniel Eduardo Viafara Guacaneme**
Universidad Manuela Beltrán — Ingeniería de Software
Docente: Jamilton Fernando Benavides · Bogotá D.C., 2026
