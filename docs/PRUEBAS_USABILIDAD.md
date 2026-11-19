# Pruebas de usabilidad — GolTime

Registro de las pruebas de usabilidad del prototipo final. Las secciones 1 a 5 son
mediciones e inspecciones sobre el sistema en funcionamiento (19 de noviembre de 2026).
La sección 6 es el protocolo de la prueba con usuarios y su registro.

Requerimientos relacionados: **RNF03** (rendimiento), **RNF04** (usabilidad) y **RNF07** (compatibilidad).

---

## 1. Recorrido de las tareas principales (RNF04)

Número de acciones necesarias para completar cada tarea, contadas desde la pantalla de inicio
de cada rol. El criterio del RNF04 es reservar en **3 pasos o menos**.

| # | Tarea | Rol | Recorrido | Acciones | Cumple |
|---|---|---|---|---|---|
| T1 | Reservar una franja | Cliente | Elegir día → elegir franja → escribir celular → Confirmar (cancha y contacto vienen preseleccionados) | 3 clics + 1 campo | Sí |
| T2 | Reservar una franja recomendada | Cliente | Reservar (en la sugerencia) → escribir celular → Confirmar | 2 clics + 1 campo | Sí |
| T3 | Cancelar una reserva | Cliente | Mis reservas → Cancelar → confirmar | 3 clics | Sí |
| T4 | Consultar el perfil de juego | Cliente | Mi juego | 1 clic | Sí |
| T5 | Ver las reservas con riesgo de cancelación | Admin | Administración (abre en Inteligencia) → bajar | 0–1 clic | Sí |
| T6 | Descargar el dataset | Admin | Dataset → Descargar CSV | 2 clics | Sí |
| T7 | Agregar una franja horaria | Admin | Franjas → Agregar franja → horas → Agregar | 3 clics + 2 campos | Sí |

## 2. Tiempos de respuesta (RNF03)

Medidos con `python scripts/medir_tiempos.py --n 30` contra PostgreSQL local (30 llamadas por
operación). Salida completa en [`evidencias/pruebas/tiempos_respuesta.txt`](evidencias/pruebas/tiempos_respuesta.txt).

| Operación | Mediana | p95 | Máximo | Criterio < 2 s |
|---|---|---|---|---|
| Consultar disponibilidad | 2,5 ms | 3,5 ms | 3,6 ms | Cumple |
| Demanda estimada (IA) | 2,4 ms | 2,8 ms | 1.345,8 ms* | Cumple |
| Mis reservas | 4,9 ms | 5,7 ms | 16,8 ms | Cumple |
| Recomendaciones (IA) | 4,2 ms | 4,4 ms | 4,8 ms | Cumple |
| Perfil de juego (IA) | 6,3 ms | 6,6 ms | 6,8 ms | Cumple |
| Tablero de IA (admin) | 7,9 ms | 9,3 ms | 10,0 ms | Cumple |
| Clientes (admin) | 7,7 ms | 8,0 ms | 8,2 ms | Cumple |
| Dataset (admin) | 11,9 ms | 12,2 ms | 13,1 ms | Cumple |

\* La primera consulta del día vuelve a entrenar los modelos (1,3 s); las siguientes usan el modelo en memoria.

## 3. Adaptación a pantallas (RNF07)

Se revisó cada vista en tres anchos y se comprobó que no aparezca desplazamiento horizontal
(ancho del documento igual al ancho de la ventana).

| Vista | Móvil 375 px | Tableta 768 px | Escritorio 1280 px |
|---|---|---|---|
| Inicio de sesión | ✔ | ✔ | ✔ |
| Reservar | ✔ | ✔ | ✔ |
| Mis reservas | ✔ | ✔ | ✔ |
| Mi juego | ✔ | ✔ | ✔ |
| Admin · Inteligencia | ✔ | ✔ | ✔ |
| Admin · Clientes | ✔ | ✔ | ✔ |
| Admin · Dataset | ✔ | ✔ | ✔ |
| Admin · Reservas | ✔ | ✔ | ✔ |
| Admin · Canchas / Franjas | ✔ | ✔ | ✔ |

En móvil la navegación muestra solo los iconos, las tarjetas pasan a una columna y las tablas
se desplazan dentro de su propio contenedor.

## 4. Contraste de color (WCAG 2.1)

| Combinación | Contraste | Nivel |
|---|---|---|
| Texto principal sobre fondo | 18,0 : 1 | AAA |
| Texto principal sobre tarjeta | 16,3 : 1 | AAA |
| Texto secundario sobre fondo | 6,6 : 1 | AA |
| Texto secundario sobre tarjeta | 6,0 : 1 | AA |
| Texto del botón principal sobre verde | 16,8 : 1 | AAA |
| Verde de marca sobre fondo | 17,3 : 1 | AAA |
| Rojo de "ocupado" sobre tarjeta | 5,3 : 1 | AA |
| Texto tenue sobre fondo / tarjeta | 5,6 : 1 / 4,7 : 1 | AA (corregido, ver H1) |

## 5. Evaluación heurística

Inspección del prototipo con las 10 heurísticas de Nielsen.

| # | Hallazgo | Heurística | Severidad | Estado |
|---|---|---|---|---|
| H1 | El texto tenue (meses en la tira de fechas, etiquetas pequeñas) tenía un contraste de 3,4 : 1, insuficiente para texto pequeño. | Diseño estético y minimalista / accesibilidad | Media | **Corregido**: el color pasó de `#5C6662` a `#808A85` (≥ 4,7 : 1). |
| H2 | La confirmación de cancelación usa el diálogo nativo del navegador, que no sigue el estilo visual del sistema. | Consistencia y estándares | Baja | Pendiente |
| H3 | Después de las 22:00 la fecha seleccionada por defecto sigue siendo "hoy", que ya no tiene franjas disponibles. | Prevención de errores | Baja | Pendiente: seleccionar el día siguiente cuando ya pasaron todas las franjas. |
| H4 | Si otra persona toma la franja mientras el cliente confirma, el sistema lo explica ("Alguien se te adelantó…") y actualiza la grilla. | Ayudar a reconocer y recuperarse de errores | — | Cumple |
| H5 | Las franjas muestran estado (disponible, reservada, ya pasó) y demanda estimada antes de reservar. | Visibilidad del estado del sistema | — | Cumple |
| H6 | Mientras se cargan los datos se muestran bloques de carga en lugar de pantallas vacías. | Visibilidad del estado del sistema | — | Cumple |
| H7 | Los datos de contacto se completan con los de la cuenta y la cancha queda preseleccionada. | Flexibilidad y eficiencia de uso | — | Cumple |

## 6. Prueba con usuarios

**Objetivo:** comprobar que un usuario que no conoce el sistema puede completar las tareas
principales sin ayuda.

**Protocolo**
1. Se explica el propósito del sistema en una frase, sin mostrar cómo se usa.
2. El participante inicia sesión con un perfil de demostración y realiza las tareas T1, T3 y T4
   (y T5, T6 si el perfil es de administrador), pensando en voz alta.
3. El moderador registra el tiempo, si completó la tarea, los errores y los comentarios, sin intervenir.
4. Al final el participante responde el cuestionario SUS (10 preguntas, escala de 1 a 5).

**Registro**

| Participante | Perfil | Tarea | Completó | Tiempo (s) | Errores | Comentarios |
|---|---|---|---|---|---|---|
| P1 | | T1 | | | | |
| P1 | | T3 | | | | |
| P1 | | T4 | | | | |
| P2 | | T1 | | | | |
| P2 | | T3 | | | | |
| P2 | | T4 | | | | |
| P3 | | T1 | | | | |
| P3 | | T3 | | | | |
| P3 | | T4 | | | | |

| Participante | Puntaje SUS (0–100) | Observaciones |
|---|---|---|
| P1 | | |
| P2 | | |
| P3 | | |

*Cálculo SUS:* en las preguntas impares se resta 1 a la respuesta y en las pares se resta la
respuesta a 5. Se suman los resultados y se multiplica por 2,5. Un puntaje mayor a 68 se
considera por encima del promedio.
