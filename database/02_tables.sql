/* =====================================================================
   Fase 2 - Tablas, claves, relaciones, restricciones e indices
   Corresponde al modelo relacional de la Fase 2:
   Usuario (1..N) Reserva (N..1) Cancha
                    Reserva (N..1) Franja
   ===================================================================== */

USE ReservaCanchas;
GO
SET ANSI_NULLS ON;
SET QUOTED_IDENTIFIER ON;   -- requerido por el indice filtrado
GO

/* Limpieza para permitir re-ejecucion (respeta el orden de las FKs) */
IF OBJECT_ID('dbo.Reserva','U') IS NOT NULL DROP TABLE dbo.Reserva;
IF OBJECT_ID('dbo.Franja','U')  IS NOT NULL DROP TABLE dbo.Franja;
IF OBJECT_ID('dbo.Cancha','U')  IS NOT NULL DROP TABLE dbo.Cancha;
IF OBJECT_ID('dbo.Usuario','U') IS NOT NULL DROP TABLE dbo.Usuario;
GO

/* -------------------------------------------------------------------
   USUARIO
   ------------------------------------------------------------------- */
CREATE TABLE dbo.Usuario (
    UsuarioId    INT IDENTITY(1,1) NOT NULL,
    Nombre       NVARCHAR(120) NOT NULL,
    Email        NVARCHAR(256) NOT NULL,
    PasswordHash NVARCHAR(200) NOT NULL,
    Rol          VARCHAR(20)   NOT NULL,
    Activo       BIT           NOT NULL CONSTRAINT DF_Usuario_Activo DEFAULT(1),
    CreadoEn     DATETIME2(3)  NOT NULL CONSTRAINT DF_Usuario_Creado DEFAULT(SYSUTCDATETIME()),
    CONSTRAINT PK_Usuario     PRIMARY KEY (UsuarioId),
    CONSTRAINT UQ_Usuario_Email UNIQUE (Email),
    CONSTRAINT CK_Usuario_Rol   CHECK (Rol IN ('cliente','admin'))
);
GO

/* -------------------------------------------------------------------
   CANCHA
   ------------------------------------------------------------------- */
CREATE TABLE dbo.Cancha (
    CanchaId   INT IDENTITY(1,1) NOT NULL,
    Nombre     NVARCHAR(100) NOT NULL,
    Superficie NVARCHAR(50)  NULL,
    Activa     BIT NOT NULL CONSTRAINT DF_Cancha_Activa DEFAULT(1),
    CONSTRAINT PK_Cancha       PRIMARY KEY (CanchaId),
    CONSTRAINT UQ_Cancha_Nombre UNIQUE (Nombre)
);
GO

/* -------------------------------------------------------------------
   FRANJA (catalogo fijo de franjas horarias)
   ------------------------------------------------------------------- */
CREATE TABLE dbo.Franja (
    FranjaId   INT IDENTITY(1,1) NOT NULL,
    HoraInicio TIME(0) NOT NULL,
    HoraFin    TIME(0) NOT NULL,
    Activa     BIT NOT NULL CONSTRAINT DF_Franja_Activa DEFAULT(1),
    CONSTRAINT PK_Franja      PRIMARY KEY (FranjaId),
    CONSTRAINT UQ_Franja      UNIQUE (HoraInicio, HoraFin),
    CONSTRAINT CK_Franja_Rango CHECK (HoraFin > HoraInicio)
);
GO

/* -------------------------------------------------------------------
   RESERVA (entidad asociativa)
   ------------------------------------------------------------------- */
CREATE TABLE dbo.Reserva (
    ReservaId   BIGINT IDENTITY(1,1) NOT NULL,
    CanchaId    INT  NOT NULL,
    FranjaId    INT  NOT NULL,
    Fecha       DATE NOT NULL,
    UsuarioId   INT  NOT NULL,
    Estado      VARCHAR(20)  NOT NULL,
    CreadaEn    DATETIME2(3) NOT NULL CONSTRAINT DF_Reserva_Creada DEFAULT(SYSUTCDATETIME()),
    CanceladaEn DATETIME2(3) NULL,
    CONSTRAINT PK_Reserva         PRIMARY KEY (ReservaId),
    CONSTRAINT CK_Reserva_Estado  CHECK (Estado IN ('confirmada','cancelada')),
    CONSTRAINT FK_Reserva_Cancha  FOREIGN KEY (CanchaId)  REFERENCES dbo.Cancha(CanchaId),
    CONSTRAINT FK_Reserva_Franja  FOREIGN KEY (FranjaId)  REFERENCES dbo.Franja(FranjaId),
    CONSTRAINT FK_Reserva_Usuario FOREIGN KEY (UsuarioId) REFERENCES dbo.Usuario(UsuarioId)
);
GO

/* -------------------------------------------------------------------
   INVARIANTE DEL SISTEMA:
   solo puede existir UNA reserva 'confirmada' por (cancha, fecha, franja).
   Las 'cancelada' no cuentan -> al cancelar se libera el cupo.
   ------------------------------------------------------------------- */
CREATE UNIQUE INDEX UX_Reserva_Slot_Confirmada
    ON dbo.Reserva (CanchaId, Fecha, FranjaId)
    WHERE Estado = 'confirmada';
GO

/* Indice de apoyo para la consulta de disponibilidad */
CREATE INDEX IX_Reserva_Consulta
    ON dbo.Reserva (CanchaId, Fecha, Estado) INCLUDE (FranjaId, UsuarioId);
GO
