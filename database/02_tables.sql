/* =====================================================================
   Tablas, claves, relaciones, restricciones e indices - PostgreSQL
   Corresponde al modelo relacional del documento maestro:
     Usuario (1..N) Reserva (N..1) Cancha
                    Reserva (N..1) Franja
   Los identificadores van entre comillas para conservar el PascalCase
   con el que la aplicacion (SQLAlchemy) crea el esquema.
   Ejecutar conectado a la base 'goltime'.
   ===================================================================== */

/* Limpieza para permitir re-ejecucion (respeta el orden de las FKs) */
DROP TABLE IF EXISTS "Reserva" CASCADE;
DROP TABLE IF EXISTS "Franja"  CASCADE;
DROP TABLE IF EXISTS "Cancha"  CASCADE;
DROP TABLE IF EXISTS "Usuario" CASCADE;

/* -------------------------------------------------------------------
   USUARIO
   ------------------------------------------------------------------- */
CREATE TABLE "Usuario" (
    "UsuarioId"    SERIAL       PRIMARY KEY,
    "Nombre"       VARCHAR(120) NOT NULL,
    "Email"        VARCHAR(256) NOT NULL UNIQUE,
    "PasswordHash" VARCHAR(200) NOT NULL,
    "Rol"          VARCHAR(20)  NOT NULL DEFAULT 'cliente',
    "Activo"       BOOLEAN      NOT NULL DEFAULT TRUE,
    "CreadoEn"     TIMESTAMP    NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    CONSTRAINT "CK_Usuario_Rol" CHECK ("Rol" IN ('cliente','admin'))
);

/* -------------------------------------------------------------------
   CANCHA
   ------------------------------------------------------------------- */
CREATE TABLE "Cancha" (
    "CanchaId"   SERIAL       PRIMARY KEY,
    "Nombre"     VARCHAR(100) NOT NULL UNIQUE,
    "Superficie" VARCHAR(50),
    "Activa"     BOOLEAN      NOT NULL DEFAULT TRUE
);

/* -------------------------------------------------------------------
   FRANJA (catalogo fijo de franjas horarias)
   ------------------------------------------------------------------- */
CREATE TABLE "Franja" (
    "FranjaId"   SERIAL  PRIMARY KEY,
    "HoraInicio" TIME    NOT NULL,
    "HoraFin"    TIME    NOT NULL,
    "Activa"     BOOLEAN NOT NULL DEFAULT TRUE,
    CONSTRAINT "UQ_Franja"       UNIQUE ("HoraInicio","HoraFin"),
    CONSTRAINT "CK_Franja_Rango" CHECK ("HoraFin" > "HoraInicio")
);

/* -------------------------------------------------------------------
   RESERVA (entidad asociativa)
   ------------------------------------------------------------------- */
CREATE TABLE "Reserva" (
    "ReservaId"   BIGSERIAL   PRIMARY KEY,
    "CanchaId"    INTEGER     NOT NULL REFERENCES "Cancha"("CanchaId"),
    "FranjaId"    INTEGER     NOT NULL REFERENCES "Franja"("FranjaId"),
    "Fecha"       DATE        NOT NULL,
    "UsuarioId"   INTEGER     NOT NULL REFERENCES "Usuario"("UsuarioId"),
    "Estado"      VARCHAR(20) NOT NULL DEFAULT 'confirmada',
    "CreadaEn"    TIMESTAMP   NOT NULL DEFAULT (now() AT TIME ZONE 'utc'),
    "CanceladaEn" TIMESTAMP,
    CONSTRAINT "CK_Reserva_Estado" CHECK ("Estado" IN ('confirmada','cancelada'))
);

/* -------------------------------------------------------------------
   INVARIANTE DEL SISTEMA:
   solo puede existir UNA reserva 'confirmada' por (cancha, fecha, franja).
   Las 'cancelada' no cuentan -> al cancelar se libera el cupo.
   Se implementa con un indice unico PARCIAL (filtrado) de PostgreSQL.
   ------------------------------------------------------------------- */
CREATE UNIQUE INDEX "UX_Reserva_Slot_Confirmada"
    ON "Reserva" ("CanchaId","Fecha","FranjaId")
    WHERE "Estado" = 'confirmada';

/* Indice de apoyo para la consulta de disponibilidad */
CREATE INDEX "IX_Reserva_Consulta"
    ON "Reserva" ("CanchaId","Fecha","Estado")
    INCLUDE ("FranjaId","UsuarioId");
