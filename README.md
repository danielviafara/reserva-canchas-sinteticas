# Sistema de Reserva de Canchas Sintéticas

![Estado](https://img.shields.io/badge/estado-en%20desarrollo-yellow)

Aplicación para reservar canchas sintéticas por franjas horarias, pensada para
evitar que dos personas terminen con el mismo turno de la misma cancha.

> Proyecto académico — Universidad Manuela Beltrán · Arquitectura de Software · Quinto semestre.

---

## ¿Qué problema resuelve?

Hoy muchas canchas gestionan sus reservas por llamadas, mensajería o cuadernos.
Cuando dos personas piden la misma franja casi al mismo tiempo, es fácil que
ambas queden confirmadas y se produzca una **doble reserva**, con los conflictos
que eso genera. Este sistema centraliza la disponibilidad para que eso no pase.

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

## Cómo está organizado

La solución se divide en tres partes: la **aplicación** con la que interactúa el
usuario, un **servidor** que procesa las reglas de la reserva, y una **base de
datos** que guarda la información y asegura que no haya turnos duplicados.

```
reserva-canchas-sinteticas/
├─ README.md
├─ docs/        # documentación y propuesta visual
├─ database/    # base de datos
├─ backend/     # servidor (FastAPI)
└─ frontend/    # aplicación (React + Vite)
```

## Autor

**Daniel Eduardo Viafara Guacaneme**
Universidad Manuela Beltrán — Ingeniería de Software
Docente: Jamilton Fernando Benavides · Bogotá D.C., 2026
