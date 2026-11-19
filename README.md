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

## Inteligencia artificial (Fase 5)

El módulo `backend/app/services/ia_service.py` aprende del historial de reservas guardado en
PostgreSQL (Python puro, sin librerías extra) y se reentrena solo cuando cambian las reservas:

| Modelo | Técnica | Dónde se ve |
|---|---|---|
| Demanda por franja | Tasa histórica por día/hora con decaimiento exponencial (vida media 6 semanas) + suavizado bayesiano + factor por cancha | Barra de demanda en cada franja de «Reservar» y mapa de calor del admin |
| Riesgo de cancelación | Regresión logística (descenso de gradiente), validación temporal 80/20, exactitud y AUC | Admin → Inteligencia |
| Tipos de jugador | K-means (k = 4) sobre frecuencia, cancelación, fin de semana, antelación y regularidad | Admin → Inteligencia |
| Recomendaciones | `afinidad × √(1 − demanda)` | Bloque «Hecho a tu medida» del jugador |

Endpoints: `GET /ia/demanda`, `GET /ia/recomendaciones`, `GET /ia/mi-perfil` (jugador) y
`GET /admin/ia`, `/admin/ia/clientes`, `/admin/ia/clientes/{id}`, `/admin/ia/dataset`, `/admin/ia/dataset.csv` (admin).

### Perfiles de demostración

Cada uno tiene ~6 meses de historia con un patrón distinto. Al entrar con uno, la pestaña
**Mi juego** muestra lo que la IA reconoce (tipo de jugador, mapa de juego, combinaciones
favoritas, riesgo del próximo partido) y le recomienda en consecuencia. El admin ve lo mismo
de cualquier cliente en **Administración → Clientes**, y el dataset completo en **→ Dataset**.

| Perfil | Correo | Contraseña | Patrón | Tipo que asigna la IA |
|---|---|---|---|---|
| Daniel | `daniel@correo.com` | `cliente123` | Martes y jueves 20:00, Cancha 1 | Fieles |
| Laura | `laura@demo.goltime.co` | `demo1234` | Sábado 19:00 y domingo 18:00, Cancha 2 | Fin de semana |
| Andrés | `andres@demo.goltime.co` | `demo1234` | Reserva mucho, con antelación, y cancela ~45 % | En riesgo |
| Camila | `camila@demo.goltime.co` | `demo1234` | Pocas reservas, sin día fijo | Ocasionales |
| Julián | `julian@demo.goltime.co` | `demo1234` | Lunes y martes 18:00 (horas flojas), Cancha 3 | Fieles |

### Pruebas

```bash
cd backend
python -m unittest tests.test_ia -v
```

17 pruebas sobre una base SQLite temporal (no tocan PostgreSQL): que el dataset respete la
regla de no doble reserva, que la IA reconozca el tipo y la rutina de cada perfil demo y le
recomiende su franja habitual, que los modelos aprendan la hora pico y los factores de
cancelación, y que la API proteja las rutas de admin y rechace la doble reserva.

### Dataset ficticio

`backend/scripts/generar_dataset.py` simula ~6 meses de reservas con patrones realistas
(viernes y 19–21 h como hora pico, efecto quincena, festivos colombianos, diciembre flojo,
cuatro arquetipos de cliente). Los usuarios sintéticos usan el dominio `@demo.goltime.co`.

```bash
cd backend
python -m scripts.generar_dataset            # genera e inserta en la BD
python -m scripts.generar_dataset --reset    # borra lo sintético y regenera
```

También exporta `database/dataset/reservas_sinteticas.csv` (incluye el arquetipo real de cada
cliente, útil para comparar con lo que descubre K-means).

### Imágenes

Coloca `hero.jpg` y `auth.jpg` en `frontend/public/img/` (ver `LEEME.md` ahí). Si no existen,
la interfaz usa un fondo de cancha generado por CSS.

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
