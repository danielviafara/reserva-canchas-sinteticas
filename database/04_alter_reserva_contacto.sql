/* =====================================================================
   Agrega los datos de contacto que se piden al reservar - PostgreSQL
   Ejecutar sobre la base 'goltime' cuando la tabla "Reserva" ya existe.
   ===================================================================== */
ALTER TABLE "Reserva" ADD COLUMN IF NOT EXISTS "NombreContacto" VARCHAR(120);
ALTER TABLE "Reserva" ADD COLUMN IF NOT EXISTS "Celular"        VARCHAR(30);
ALTER TABLE "Reserva" ADD COLUMN IF NOT EXISTS "CorreoContacto" VARCHAR(256);
