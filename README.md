# GolTime — Sistema de Reserva de Canchas Sintéticas

![Estado](https://img.shields.io/badge/estado-entrega%20final-brightgreen)
![Pruebas](https://img.shields.io/badge/pruebas-18%20OK-brightgreen)

Sistema transaccional para reservar canchas sintéticas por franjas horarias que **impide la
doble reserva aun con acceso concurrente**, con un **servicio de inteligencia artificial** que
aprende del histórico de reservas para predecir la demanda y recomendarle a cada jugador los
horarios que mejor se ajustan a su forma de jugar.

> Proyecto académico — Universidad Manuela Beltrán · Sistemas Transaccionales · Quinto semestre.

| | |
|---|---|
| 📄 Documento Maestro final | [`docs/Documento_Maestro_GolTime.pdf`](docs/Documento_Maestro_GolTime.pdf) |
| 🧪 Pruebas de usabilidad | [`docs/PRUEBAS_USABILIDAD.md`](docs/PRUEBAS_USABILIDAD.md) |
| 🖼️ Evidencias (prototipo, IA y pruebas) | [`docs/evidencias/`](docs/evidencias/) |
| 📊 Dataset de entrenamiento | [`database/dataset/reservas_sinteticas.csv`](database/dataset/reservas_sinteticas.csv) |

---

## Funcionalidades

**Cliente**
- Reserva en tres bloques: cancha → día (próximas 2 semanas) → hora, con la demanda estimada por la IA en cada franja.
- Confirmación con datos de contacto; aviso claro si otra persona tomó la franja primero (409).
- *Mis reservas*: próximos partidos, historial y cancelación.
- *Mi juego*: tipo de jugador, patrón detectado, mapa de juego, riesgo del próximo partido y recomendaciones que abren la reserva directamente.

**Administrador**
- *Inteligencia*: ocupación, hallazgos de la IA, mapa de demanda, pronóstico de 7 días, reservas con riesgo de cancelación, pesos del modelo y tipos de jugador.
- *Clientes*: tipo y patrón de cada cliente, con su perfil completo.
- *Dataset*: distribuciones, muestra, diccionario de datos y descarga en CSV.
- *Reservas*, *Canchas* y *Franjas*: gestión y cancelación.

## Servicio de inteligencia artificial

Módulo [`backend/app/services/ia_service.py`](backend/app/services/ia_service.py), en Python
puro. Lee las reservas de PostgreSQL, entrena en memoria en menos de un segundo y se vuelve a
entrenar cuando cambian las reservas. **No escribe en la base de datos ni participa en la transacción de reserva.**

| Modelo | Técnica | Resultado |
|---|---|---|
| Demanda por franja | Tasa histórica por día/hora con decaimiento exponencial, suavizado bayesiano y factor por cancha | Probabilidad de ocupación |
| Riesgo de cancelación | Regresión logística (descenso de gradiente), validación temporal 80/20 | Probabilidad de cancelación · AUC 0,66 · detecta 2,1× más que el azar |
| Tipos de jugador | K-means (k = 4) sobre frecuencia, cancelación, fin de semana, antelación y regularidad | Fieles, Fin de semana, En riesgo, Ocasionales |
| Recomendación | Coincidencia con los hábitos × cancha favorita × √(1 − demanda) | 3 franjas libres con su motivo |

Rutas: `GET /ia/demanda`, `/ia/recomendaciones`, `/ia/mi-perfil` (jugador) ·
`GET /admin/ia`, `/admin/ia/clientes`, `/admin/ia/clientes/{id}`, `/admin/ia/dataset`, `/admin/ia/dataset.csv` (admin).

### Dataset ficticio

[`backend/scripts/generar_dataset.py`](backend/scripts/generar_dataset.py) simula 6 meses de
operación con reglas realistas (viernes y 19–21 h como hora pico, quincena, festivos
colombianos, diciembre flojo, Cancha 1 favorita) y nunca genera dos reservas confirmadas en el
mismo cupo. Incluye 115 clientes por arquetipo y 5 perfiles demo con patrones marcados:

| Perfil | Correo | Contraseña | Patrón | Tipo que asigna la IA |
|---|---|---|---|---|
| Administrador | `admin@goltime.com` | `admin123` | — | — |
| Daniel | `daniel@correo.com` | `cliente123` | Martes y jueves 20:00, Cancha 1 | Fieles |
| Laura | `laura@demo.goltime.co` | `demo1234` | Sábado 19:00 y domingo 18:00, Cancha 2 | Fin de semana |
| Andrés | `andres@demo.goltime.co` | `demo1234` | Reserva mucho, con antelación, y cancela ~50 % | En riesgo |
| Camila | `camila@demo.goltime.co` | `demo1234` | Pocas reservas, sin día fijo | Ocasionales |
| Julián | `julian@demo.goltime.co` | `demo1234` | Lunes y martes 18:00, Cancha 3 | Fieles |

```bash
cd backend
python -m scripts.generar_dataset            # genera e inserta en la BD
python -m scripts.generar_dataset --reset    # borra lo sintético y regenera
```

## Cómo ejecutar

Requisitos: Python 3.11+, Node 18+ y PostgreSQL (o SQLite para una prueba rápida).

```bash
# 1. Backend — http://localhost:8000 (documentación en /docs)
cd backend
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env                                # ajusta DATABASE_URL y JWT_SECRET
uvicorn app.main:app --reload
python -m scripts.generar_dataset                   # carga el dataset (una vez)

# 2. Frontend — http://localhost:5173
cd frontend
npm install
npm run dev
```

Al iniciar, el backend crea las tablas y carga los datos base (3 canchas, 4 franjas, administrador y Daniel).

## Pruebas

```bash
cd backend
python scripts/test_concurrencia.py --n 10   # con el backend corriendo
python -m unittest tests.test_ia -v          # usa una SQLite temporal
python scripts/medir_tiempos.py --n 30       # tiempos de respuesta (RNF03)
```

- **Concurrencia:** 10 reservas simultáneas de 5 usuarios sobre la misma franja → 1 confirmada (201) y 9 rechazadas (409). Al final cancela la reserva ganadora para dejar los datos como estaban.
- **18 pruebas automáticas:** integridad del dataset, concurrencia, doble reserva, seguridad de rutas, patrones de los perfiles demo, recomendaciones y aprendizaje de los modelos.
- **Usabilidad:** recorrido de tareas, tiempos de respuesta, adaptación a pantallas, contraste y evaluación heurística en [`docs/PRUEBAS_USABILIDAD.md`](docs/PRUEBAS_USABILIDAD.md).

Para ver las transacciones en consola (BEGIN, INSERT, COMMIT, ROLLBACK) pon `SQL_ECHO=true` en el `.env`.

## Control de la doble reserva

1. El cliente elige una franja libre y confirma.
2. El backend verifica dentro de una transacción que la franja siga libre y la registra.
3. Si dos solicitudes llegan a la vez, el **índice único filtrado** `UX_Reserva_Slot_Confirmada`
   (una sola reserva `confirmada` por cancha, fecha y franja) rechaza la segunda y la API responde `409`.

## Estructura

```
reserva-canchas-sinteticas/
├─ backend/                      API FastAPI por capas
│  ├─ app/
│  │  ├─ api/routes/             auth, canchas, disponibilidad, reservas, admin, ia
│  │  ├─ core/                   configuración y seguridad JWT
│  │  ├─ db/                     sesión, modelos ORM y datos base
│  │  ├─ schemas/                validación Pydantic
│  │  ├─ repositories/           acceso a datos
│  │  └─ services/               reserva, autenticación, administración e IA (ia_service)
│  ├─ scripts/                   generar_dataset.py · test_concurrencia.py · medir_tiempos.py
│  └─ tests/                     test_ia.py (18 pruebas)
├─ frontend/                     aplicación React + Vite
│  └─ src/
│     ├─ assets/siluetas/        siluetas de jugadores de la identidad visual
│     ├─ components/             Auth, Navbar, Disponibilidad, MisReservas, MiJuego,
│     │                          Admin, AdminIA, AdminDatos, Icon, Silueta
│     ├─ api.js                  capa de acceso a la API
│     ├─ utils.js                fechas en hora local
│     └─ styles.css              sistema visual de la marca
├─ database/                     scripts SQL de PostgreSQL y dataset exportado
└─ docs/                         documento maestro, pruebas de usabilidad y evidencias
```

## Tecnologías

React + Vite · FastAPI · SQLAlchemy · PostgreSQL · JWT · Python (modelos de IA sin dependencias externas).

## Autor

**Daniel Eduardo Viafara Guacaneme** — Universidad Manuela Beltrán, Ingeniería de Software.
Docente: Jamilton Fernando Benavides · Bogotá D.C., 2026
