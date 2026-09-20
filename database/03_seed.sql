/* =====================================================================
   Fase 2 - Datos iniciales de prueba
   Nota: los PasswordHash son valores de demostracion (no son claves reales).
   ===================================================================== */

USE ReservaCanchas;
GO

/* Usuarios: 1 administrador y 2 clientes */
INSERT INTO dbo.Usuario (Nombre, Email, PasswordHash, Rol) VALUES
    ('Administrador', 'admin@canchas.com',  '$2b$12$demoHashAdmin000000000000000000000000000000000000000', 'admin'),
    ('Daniel Viafara','daniel@correo.com',  '$2b$12$demoHashCli1000000000000000000000000000000000000000',  'cliente'),
    ('Laura Gomez',   'laura@correo.com',   '$2b$12$demoHashCli2000000000000000000000000000000000000000',  'cliente');

/* Canchas */
INSERT INTO dbo.Cancha (Nombre, Superficie) VALUES
    ('Cancha 1', 'Cesped sintetico'),
    ('Cancha 2', 'Cesped sintetico'),
    ('Cancha 3', 'Cesped sintetico');

/* Franjas horarias (catalogo fijo, 1 hora cada una) */
INSERT INTO dbo.Franja (HoraInicio, HoraFin) VALUES
    ('18:00','19:00'),
    ('19:00','20:00'),
    ('20:00','21:00'),
    ('21:00','22:00');

/* Reservas de ejemplo
   - dos confirmadas
   - una cancelada (muestra que el cupo queda libre de nuevo) */
INSERT INTO dbo.Reserva (CanchaId, FranjaId, Fecha, UsuarioId, Estado) VALUES
    (1, 3, '2026-09-20', 2, 'confirmada'),   -- Cancha 1, 20:00-21:00, Daniel
    (2, 1, '2026-09-20', 3, 'confirmada');   -- Cancha 2, 18:00-19:00, Laura

INSERT INTO dbo.Reserva (CanchaId, FranjaId, Fecha, UsuarioId, Estado, CanceladaEn) VALUES
    (1, 4, '2026-09-20', 3, 'cancelada', SYSUTCDATETIME()); -- cupo liberado
GO

/* Verificacion rapida */
SELECT c.Nombre AS Cancha, f.HoraInicio, f.HoraFin, r.Fecha, u.Nombre AS Usuario, r.Estado
FROM dbo.Reserva r
JOIN dbo.Cancha  c ON c.CanchaId = r.CanchaId
JOIN dbo.Franja  f ON f.FranjaId = r.FranjaId
JOIN dbo.Usuario u ON u.UsuarioId = r.UsuarioId
ORDER BY c.Nombre, f.HoraInicio;
GO
