# GolTime — Sistema de Reserva de Canchas Sintéticas

![Estado](https://img.shields.io/badge/estado-interfaz%20%2B%20operaci%C3%B3n%20de%20reserva-brightgreen)

Aplicación para reservar canchas sintéticas por franjas horarias, pensada para
evitar que dos personas terminen con el mismo turno de la misma cancha.

> Proyecto académico — Universidad Manuela Beltrán · Sistemas Transaccionales · Quinto semestre.

---

## Novedades de esta fase (Fase 4)

- **Diseño y navegabilidad de la interfaz** (React + Vite): menú principal con navegación
  entre Disponibilidad y Mis reservas, estados activos, y mensajes claros de éxito y error.
- **Integración con la base de datos consolidada en PostgreSQL:** registro de usuarios,
  consulta y visualización de reservas desde la aplicación, con validación de los datos
  antes de enviarlos y manejo básico de errores de conexión y de operación.
- **Operación principal:** consultar disponibilidad y **reservar una franja**, con el control
  que impide la **doble reserva** (RF04 y RF05 del documento maestro).
- **Scripts SQL actualizados a PostgreSQL** en `database/`, acordes con el esquema real.
- La configuración sensible (conexión y clave JWT) se maneja por variables de entorno en un
  `.env` local excluido de Git.

## Tecnologías

- **Frontend:** React + Vite
- **Backend:** FastAPI (Python) · SQLAlchemy
- **Base de datos:** PostgreSQL
- **Autenticación:** JWT

## Estructura

```
reserva-canchas-sinteticas/
├─ frontend/        # aplicación React + Vite
│  └─ src/
│     ├─ components/  (Auth, Navbar, Disponibilidad, MisReservas)
│     ├─ api.js       (capa de acceso a la API)
│     └─ styles.css
├─ backend/         # API FastAPI por capas
│  └─ app/
│     ├─ api/          (rutas y dependencias)
│     ├─ core/         (config, seguridad JWT)
│     ├─ db/           (sesión, modelos, seed)
│     ├─ schemas/      (validación Pydantic)
│     ├─ repositories/ (acceso a datos)
│     └─ services/     (lógica de reserva y autenticación)
├─ database/        # scripts SQL de la base de datos
└─ docs/            # documentación del proyecto
```

## Cómo ejecutar

### 1. Backend (API)

```bash
cd backend
python -m venv .venv
source .venv/bin/activate          # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                # ajusta la conexión a PostgreSQL
uvicorn app.main:app --reload
```

La API queda en `http://localhost:8000` (documentación interactiva en `/docs`).
Al iniciar crea las tablas y carga datos de prueba (3 canchas, 4 franjas y 2 usuarios).

Usuarios de prueba:
- Cliente — `daniel@correo.com` / `cliente123`
- Administrador — `admin@goltime.com` / `admin123`

### 2. Frontend (aplicación)

```bash
cd frontend
npm install
npm run dev
```

La aplicación queda en `http://localhost:5173` y habla con el backend a través de `/api`.

### 3. Probar el control de concurrencia (opcional)

Con el backend corriendo, en otra terminal:

```bash
cd backend
python scripts/test_concurrencia.py
```

Dispara dos reservas sobre la misma franja a la vez y debe mostrar una confirmada (201)
y una rechazada (409), evidenciando que no se produce la doble reserva.

## Base de datos

Al iniciar, el backend crea las tablas automáticamente desde los modelos (SQLAlchemy) y
carga datos de prueba. Como evidencia del modelo relacional, en `database/` están los
scripts SQL equivalentes para **PostgreSQL**:

```bash
psql -U usuario -d postgres -f database/01_create_database.sql
psql -U usuario -d goltime  -f database/02_tables.sql
psql -U usuario -d goltime  -f database/03_seed.sql
```

Para **evidenciar las transacciones** en consola (BEGIN, INSERT, COMMIT, ROLLBACK), basta
con poner `SQL_ECHO=true` en el `.env` y reiniciar el backend.

## Operación principal: reservar una franja

1. El cliente inicia sesión y consulta la disponibilidad de una cancha para una fecha.
2. Selecciona una franja libre y confirma.
3. El backend verifica, dentro de una transacción, que la franja siga libre y la registra.
4. Si otra persona la tomó primero, responde `409` y la aplicación vuelve a sincronizar la grilla.

El invariante "una sola reserva confirmada por cancha, fecha y franja" se respalda con un
índice único filtrado en la base de datos.

## Autor

**Daniel Eduardo Viafara Guacaneme** — Universidad Manuela Beltrán, Ingeniería de Software.
Docente: Jamilton Fernando Benavides · Bogotá D.C., 2026
