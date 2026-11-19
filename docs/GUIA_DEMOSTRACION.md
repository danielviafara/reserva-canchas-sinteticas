# Guía de demostración — Presentación final

Guion para la socialización en vivo: **prototipo**, **pruebas** y **servicio de IA**.
Duración sugerida: 12–15 minutos.

## Antes de empezar (5 minutos antes)

```bash
# Terminal 1 — backend
cd backend && source .venv/bin/activate
uvicorn app.main:app --reload --port 8000

# Terminal 2 — frontend
cd frontend && npm run dev
```

Abrir `http://localhost:5173`. Si se quieren los datos "como nuevos" para la demo:

```bash
cd backend && python -m scripts.generar_dataset --reset
```

## 1. Prototipo — procesos transaccionales (4 min)

| Paso | Usuario | Qué mostrar |
|---|---|---|
| 1 | — | Pantalla de inicio: perfiles de demostración con un clic. |
| 2 | Daniel | **Reservar**: bloques 01 Cancha → 02 Fecha → 03 Hora. Franjas libres vs. reservadas. |
| 3 | Daniel | Tocar una franja libre → boleta + datos de contacto → **Confirmar**. Mensaje de éxito. |
| 4 | Daniel | **Mis reservas**: aparece la reserva; **Cancelar** libera el cupo. |
| 5 | Admin | **Administración → Reservas** (búsqueda y filtros), **Canchas** y **Franjas**. |

Frase clave: *"La reserva se registra dentro de una transacción y el índice único filtrado
garantiza una sola reserva confirmada por cancha, fecha y franja."*

## 2. Pruebas (3 min)

```bash
# Terminal 3 — con el backend corriendo
cd backend
python scripts/test_concurrencia.py --n 10     # 10 reservas simultáneas sobre la misma franja
python -m unittest tests.test_ia -v            # 18 pruebas automáticas (SQLite temporal)
```

Resultado esperado: **1 confirmada (201) y 9 rechazadas (409)**, y `Ran 18 tests ... OK`.
La prueba de concurrencia cancela la reserva ganadora al final, así que se puede repetir.

## 3. Servicio de Inteligencia Artificial (5 min)

**Demostración**

1. **Daniel → Reservar**: bloque *Hecho a tu medida* y la barra de demanda en cada franja.
2. **Daniel → Mi juego**: tipo *Fieles*, patrón "martes y jueves 20:00, Cancha 1", mapa de
   juego, riesgo del próximo partido y recomendación de su clásico → **Reservar** abre la franja.
3. Cambiar a **Laura** (Fin de semana) o **Andrés** (En riesgo): otro patrón, otras recomendaciones.
4. **Admin → Inteligencia**: hallazgos, mapa de demanda, pronóstico 7 días, riesgo de
   cancelación y pesos del modelo, tipos de jugador. Desplegar *Cómo funciona la IA*.
5. **Admin → Clientes** (perfil de cualquier cliente) y **→ Dataset** (descargar CSV).

**Las 5 preguntas**

| Pregunta | Respuesta corta |
|---|---|
| ¿Qué problema resuelve? | Además de evitar la doble reserva, ayuda a aprovechar las canchas: anticipa qué franjas se llenan, qué reservas se van a caer y qué horario le sirve a cada cliente. |
| ¿Cómo se integra? | Módulo `ia_service` del servidor FastAPI. Lee las reservas de PostgreSQL, entrena en memoria (< 1 s) y expone `/ia/*` y `/admin/ia/*`. No escribe ni participa en la transacción. |
| ¿Qué información procesa? | El histórico de reservas: fecha, día, franja, cancha, estado, antelación y cliente (1.523 reservas, 121 clientes). |
| ¿Qué resultado genera? | Probabilidad de ocupación por franja, probabilidad de cancelación por reserva, tipo de jugador (K-means) y franjas recomendadas con su motivo. |
| ¿Cómo usa el sistema ese resultado? | El cliente ve la demanda y sus recomendaciones (reserva con un clic) y su perfil en *Mi juego*. El admin ve el tablero, los clientes en riesgo y el dataset. |

**Si preguntan por la red neuronal**: la regresión logística es la neurona de salida con
sigmoide del diseño (Figura 9 del documento). Con ~1.500 reservas una red con capas ocultas
memorizaría los datos; una sola neurona es explicable (se ven los pesos) y entrena en menos
de un segundo. Las capas ocultas quedan para cuando haya histórico real.

## Usuarios

| Perfil | Correo | Contraseña |
|---|---|---|
| Administrador | `admin@goltime.com` | `admin123` |
| Daniel (Fiel) | `daniel@correo.com` | `cliente123` |
| Laura (Fin de semana) | `laura@demo.goltime.co` | `demo1234` |
| Andrés (En riesgo) | `andres@demo.goltime.co` | `demo1234` |
| Camila (Ocasional) | `camila@demo.goltime.co` | `demo1234` |
| Julián (Fiel, 18:00) | `julian@demo.goltime.co` | `demo1234` |
