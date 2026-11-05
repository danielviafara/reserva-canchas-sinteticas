/* =====================================================================
   Datos iniciales de prueba - PostgreSQL
   Nota: los PasswordHash son valores de demostracion (no son claves reales).
   Ejecutar conectado a la base 'goltime', despues de 02_tables.sql.
   ===================================================================== */

/* Usuarios: 1 administrador y 2 clientes */
INSERT INTO "Usuario" ("Nombre","Email","PasswordHash","Rol") VALUES
    ('Administrador', 'admin@canchas.com',  '$2b$12$demoHashAdmin000000000000000000000000000000000000000', 'admin'),
    ('Daniel Viafara','daniel@correo.com',  '$2b$12$demoHashCli1000000000000000000000000000000000000000',  'cliente'),
    ('Laura Gomez',   'laura@correo.com',   '$2b$12$demoHashCli2000000000000000000000000000000000000000',  'cliente');

/* Canchas */
INSERT INTO "Cancha" ("Nombre","Superficie") VALUES
    ('Cancha 1', 'Cesped sintetico'),
    ('Cancha 2', 'Cesped sintetico'),
    ('Cancha 3', 'Cesped sintetico');

/* Franjas horarias (catalogo fijo, 1 hora cada una) */
INSERT INTO "Franja" ("HoraInicio","HoraFin") VALUES
    ('18:00','19:00'),
    ('19:00','20:00'),
    ('20:00','21:00'),
    ('21:00','22:00');

/* Reservas de ejemplo: dos confirmadas y una cancelada (cupo liberado) */
INSERT INTO "Reserva" ("CanchaId","FranjaId","Fecha","UsuarioId","Estado") VALUES
    (1, 3, '2026-09-20', 2, 'confirmada'),
    (2, 1, '2026-09-20', 3, 'confirmada');

INSERT INTO "Reserva" ("CanchaId","FranjaId","Fecha","UsuarioId","Estado","CanceladaEn") VALUES
    (1, 4, '2026-09-20', 3, 'cancelada', now() AT TIME ZONE 'utc');

/* Verificacion rapida */
SELECT c."Nombre" AS cancha, f."HoraInicio", f."HoraFin", r."Fecha",
       u."Nombre" AS usuario, r."Estado"
FROM "Reserva" r
JOIN "Cancha"  c ON c."CanchaId"  = r."CanchaId"
JOIN "Franja"  f ON f."FranjaId"  = r."FranjaId"
JOIN "Usuario" u ON u."UsuarioId" = r."UsuarioId"
ORDER BY c."Nombre", f."HoraInicio";
