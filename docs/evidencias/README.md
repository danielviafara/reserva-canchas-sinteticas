# Evidencias de la entrega final

Capturas del prototipo en funcionamiento y salidas de las pruebas (18 de noviembre de 2026).
Las figuras del Documento Maestro se tomaron de esta carpeta.

## `prototipo/` — procesos transaccionales

| Archivo | Qué muestra |
|---|---|
| `01_inicio_sesion.jpg` | Inicio de sesión con perfiles de demostración (Fig. 14) |
| `02_reservar_portada.jpg` | Portada de la pantalla de reserva |
| `04_bloques_cancha_fecha.jpg` | Bloques 01 Cancha y 02 Fecha (Fig. 15) |
| `05_franjas_demanda_ia.jpg` | Franjas libres/reservadas con demanda estimada (Fig. 16) |
| `06_confirmar_reserva.jpg` | Boleta y datos de contacto (Fig. 17) |
| `07_reserva_confirmada.jpg` | Mensaje de reserva confirmada |
| `08_mis_reservas.jpg` | Próximas reservas con opción de cancelar (Fig. 18) |

## `ia/` — servicio de inteligencia artificial

| Archivo | Qué muestra |
|---|---|
| `03_ia_sugerencias_cliente.jpg` | Recomendaciones en la pantalla de reserva (Fig. 19) |
| `09_mi_juego_perfil.jpg` | Tipo de jugador y patrón detectado (Fig. 20) |
| `10_mi_juego_mapa.jpg` | Mapa de juego y últimos 6 meses (Fig. 21) |
| `11_mi_juego_recomendacion.jpg` | Favoritos, riesgo del próximo partido y recomendación (Fig. 22) |
| `12_admin_ia_kpis.jpg` | Panel de Inteligencia y hallazgos (Fig. 23) |
| `13_admin_demanda_pronostico.jpg` | Mapa de demanda y pronóstico 7 días (Fig. 10) |
| `14_admin_riesgo_cancelacion.jpg` | Riesgo de cancelación y pesos del modelo (Fig. 11) |
| `15_admin_segmentos.jpg` | Tipos de jugador (K-means) (Fig. 12) |
| `16_admin_clientes.jpg` | Clientes con su tipo y patrón (Fig. 24) |
| `17_admin_dataset.jpg` | Dataset de entrenamiento (Fig. 13) |

## `pruebas/`

| Archivo | Qué muestra |
|---|---|
| `18_prueba_concurrencia.jpg` / `prueba_concurrencia.txt` | 10 reservas simultáneas: 1 confirmada, 9 rechazadas (Fig. 25) |
| `19_pruebas_automaticas.jpg` / `pruebas_automaticas.txt` | 18 pruebas automáticas OK (Fig. 26) |
| `tiempos_respuesta.txt` | Tiempos de respuesta de las operaciones principales (RNF03) |

Para regenerarlas: `python scripts/test_concurrencia.py --n 10` y
`python -m unittest tests.test_ia -v` desde `backend/`.
