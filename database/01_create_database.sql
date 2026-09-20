/* =====================================================================
   Fase 2 - Creacion de la base de datos
   Sistema de Reserva de Canchas Sinteticas
   ===================================================================== */

IF DB_ID('ReservaCanchas') IS NULL
    CREATE DATABASE ReservaCanchas;
GO

USE ReservaCanchas;
GO
