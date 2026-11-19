"""Generador de un dataset FICTICIO de reservas para entrenar y demostrar el modulo de IA.

Simula ~6 meses de historia de GolTime con patrones realistas de una cancha
sintetica en Colombia, para que los modelos tengan algo que aprender:

  * Demanda por dia de la semana: viernes y sabado son los mas fuertes, lunes el mas flojo.
  * Demanda por hora: 19:00 y 20:00 son la hora pico (salida del trabajo).
  * Efecto "quincena": los dias 14-16 y 29-31 (y 1) del mes sube la demanda.
  * Festivos colombianos (Ley Emiliani): bajan la demanda nocturna.
  * Diciembre: baja la demanda (vacaciones).
  * Cancha 1 es la favorita (mejor iluminacion, la mas cercana a la entrada).

Hay dos tipos de clientes:

1. PERFILES DEMO (con nombre propio y contrasena conocida) con un patron de juego
   muy marcado, pensados para la sustentacion: al entrar con cada uno se ve como la
   IA reconoce su patron y le recomienda en consecuencia.

       daniel@correo.com        Fiel entre semana: martes y jueves 20:00, Cancha 1
       laura@demo.goltime.co    Fin de semana: sabado 19:00 y domingo 18:00, Cancha 2
       andres@demo.goltime.co   En riesgo: reserva mucho, con antelacion, en cualquier dia, y cancela a menudo
       camila@demo.goltime.co   Ocasional: pocas reservas, sin dia ni hora fijos
       julian@demo.goltime.co   Cazador de cupos: lunes y martes 18:00 (horas flojas), Cancha 3

   Para que la demostracion sea estable, cada perfil tiene reservado solo su PROXIMO
   partido habitual; las siguientes franjas habituales se dejan libres (ningun cliente
   de la "multitud" las toma), asi la IA siempre tiene algo concreto que recomendarles.

2. LA MULTITUD: ~115 clientes generados al azar por arquetipo (fiel, fin de semana,
   ocasional, impredecible) que llenan el resto de la cancha.

La cancelacion depende de la antelacion, del cliente y del dia -> es lo que aprende
la regresion logistica del modulo de IA.

Uso (desde backend/ con el venv activo):
    python -m scripts.generar_dataset            # genera e inserta
    python -m scripts.generar_dataset --reset    # borra lo sintetico y regenera
    python -m scripts.generar_dataset --solo-csv # solo escribe el CSV, no toca la BD

Contrasena de todos los usuarios demo: demo1234 (Daniel conserva cliente123).
Todo lo generado se puede borrar sin tocar los datos reales: usuarios @demo.goltime.co
y las reservas demo de Daniel (celular 310555xxxx).
"""
import argparse
import csv
import math
import random
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db import models  # noqa: E402
from app.db.seed import seed  # noqa: E402
from app.db.session import Base, SessionLocal, engine  # noqa: E402

SEMILLA = 2026
DIAS_HISTORIA = 180
DIAS_FUTURO = 14
DOMINIO = "@demo.goltime.co"
PREFIJO_CEL_DEMO = "310555"
CLAVE_DEMO = "demo1234"
CSV_SALIDA = Path(__file__).resolve().parents[2] / "database" / "dataset" / "reservas_sinteticas.csv"

# ------------------------------------------------------------------ perfiles demo
# habitos: (dia_semana 0=lunes, hora_inicio, indice_de_cancha, probabilidad semanal)
PERFILES_DEMO = [
    {"email": "daniel@correo.com", "nombre": "Daniel Viafara", "perfil": "Fiel entre semana",
     "habitos": [(1, 20, 0, 0.92), (3, 20, 0, 0.88)], "extra": 0.015, "antelacion": 5.0, "p_cancel": 0.04},
    {"email": "laura" + DOMINIO, "nombre": "Laura Gómez", "perfil": "Fin de semana",
     "habitos": [(5, 19, 1, 0.88), (6, 18, 1, 0.65)], "extra": 0.008, "antelacion": 2.0, "p_cancel": 0.07},
    {"email": "andres" + DOMINIO, "nombre": "Andrés Rojas", "perfil": "En riesgo",
     "habitos": [(4, 20, 0, 0.45)], "extra": 0.16, "antelacion": 9.0, "p_cancel": 0.3},
    {"email": "camila" + DOMINIO, "nombre": "Camila Ortiz", "perfil": "Ocasional",
     "habitos": [], "extra": 0.05, "antelacion": 0.4, "p_cancel": 0.08},
    {"email": "julian" + DOMINIO, "nombre": "Julián Torres", "perfil": "Cazador de cupos libres",
     "habitos": [(0, 18, 2, 0.9), (1, 18, 2, 0.6)], "extra": 0.01, "antelacion": 1.5, "p_cancel": 0.04},
]

NOMBRES = ["Santiago", "Sebastián", "Mateo", "Nicolás", "Alejandro", "Samuel", "Juan David", "Daniel",
           "Andrés", "Felipe", "Camilo", "Julián", "Esteban", "Tomás", "Miguel", "Cristian", "Kevin",
           "Brayan", "Jhon", "Óscar", "Valentina", "Laura", "Mariana", "Daniela", "Natalia", "Paula",
           "Sara", "Juliana", "Carolina", "Manuela"]
APELLIDOS = ["Gómez", "Rodríguez", "Martínez", "López", "García", "Hernández", "Díaz", "Moreno",
             "Muñoz", "Rojas", "Vargas", "Castro", "Ortiz", "Ramírez", "Torres", "Quintero", "Mosquera",
             "Valencia", "Cárdenas", "Ospina", "Restrepo", "Zapata", "Caicedo", "Mejía"]

# Peso relativo por dia (lunes=0 ... domingo=6) y por hora de inicio.
PESO_DIA = [0.55, 0.70, 0.78, 0.88, 1.18, 1.10, 0.80]
PESO_HORA = {18: 0.72, 19: 1.12, 20: 1.15, 21: 0.78}
PESO_CANCHA = [1.15, 1.00, 0.85]  # por orden de CanchaId
OCUPACION_BASE = 0.74

ARQUETIPOS = {
    #                 cuantos, actividad, antelacion (media dias), prob. cancelar base
    "fiel":          (22, 3.2, 5.0, 0.04),
    "fin_de_semana": (30, 1.6, 2.5, 0.10),
    "ocasional":     (45, 0.6, 0.6, 0.12),
    "impredecible":  (18, 1.8, 8.0, 0.32),
}


def lunes_siguiente(d: date) -> date:
    return d if d.weekday() == 0 else d + timedelta(days=7 - d.weekday())


def festivos(anio: int) -> set:
    """Festivos colombianos de fecha fija y los trasladados a lunes (Ley Emiliani).
    No incluye los que dependen de Semana Santa (no caen en la ventana simulada)."""
    fijos = {date(anio, 1, 1), date(anio, 5, 1), date(anio, 7, 20), date(anio, 8, 7),
             date(anio, 12, 8), date(anio, 12, 25)}
    trasladables = [date(anio, 1, 6), date(anio, 3, 19), date(anio, 6, 29), date(anio, 8, 15),
                    date(anio, 10, 12), date(anio, 11, 1), date(anio, 11, 11)]
    return fijos | {lunes_siguiente(d) for d in trasladables}


def factor_fecha(d: date, fest: set) -> float:
    f = PESO_DIA[d.weekday()]
    if d.day in (14, 15, 16, 29, 30, 31, 1):
        f *= 1.12  # quincena
    if d in fest:
        f *= 0.70
    if d.month == 12 and d.day >= 15:
        f *= 0.75
    return f


def crear_multitud(rng: random.Random, franjas):
    """Cada cliente tiene un arquetipo y, si aplica, un dia/hora favoritos."""
    clientes, usados = [], set()
    horas = [f.HoraInicio.hour for f in franjas]
    for arq, (n, actividad, antel, pcancel) in ARQUETIPOS.items():
        for _ in range(n):
            while True:
                nom, ape = rng.choice(NOMBRES), rng.choice(APELLIDOS)
                if (nom, ape) not in usados:
                    usados.add((nom, ape))
                    break
            slug = (f"{nom}.{ape}".lower().replace(" ", "")
                    .translate(str.maketrans("áéíóúñ", "aeioun")))
            if arq == "fin_de_semana":
                dias_fav = rng.sample([4, 5, 6], 2)
            elif arq == "fiel":
                dias_fav = [rng.choice([0, 1, 2, 3, 4])]
            else:
                dias_fav = list(range(7))
            clientes.append({
                "nombre": f"{nom} {ape}", "email": slug + DOMINIO, "perfil": arq,
                "actividad": actividad * rng.uniform(0.7, 1.3), "antelacion": antel,
                "p_cancel": pcancel, "dias_fav": dias_fav,
                "hora_fav": rng.choice([19, 20]) if arq == "fiel" else rng.choice(horas),
                "celular": "32" + "".join(str(rng.randint(0, 9)) for _ in range(8)),
            })
    return clientes


def afinidad(c, d: date, hora: int) -> float:
    a = c["actividad"]
    if d.weekday() in c["dias_fav"]:
        a *= 4.0 if c["perfil"] == "fiel" else 1.6
    elif c["perfil"] in ("fiel", "fin_de_semana"):
        a *= 0.08
    if hora == c["hora_fav"]:
        a *= 2.2
    return a


def prob_cancelar(p_base: float, antelacion_dias: float, d: date) -> float:
    z = math.log(p_base / (1 - p_base))
    z += 0.11 * antelacion_dias            # mas antelacion -> mas cancelacion
    z += 0.35 if d.weekday() == 6 else 0   # domingo: se cae mas el plan
    return 1 / (1 + math.exp(-z))


class Simulador:
    def __init__(self, rng, canchas, franjas, ocupados):
        self.rng, self.canchas, self.franjas = rng, canchas, franjas
        self.ocupados = set(ocupados)   # (cancha_id, franja_id, fecha) confirmadas
        self.protegidos = set()         # cupos futuros reservados "para la demo"
        self.por_hora = {f.HoraInicio.hour: f for f in franjas}
        self.ahora = datetime.now()
        self.filas = []

    def intentar(self, cliente, cancha, franja, d, antel_media, p_cancel, antel_min=0.05, antel_max=21.0):
        """Intenta que `cliente` reserve. Devuelve True si el cupo quedo ocupado."""
        clave = (cancha.CanchaId, franja.FranjaId, d)
        if clave in self.ocupados:
            return False
        antel = min(antel_max, max(antel_min, self.rng.expovariate(1 / max(0.3, antel_media))))
        inicio = datetime.combine(d, franja.HoraInicio)
        creada = inicio - timedelta(days=antel)
        if creada > self.ahora:
            return False  # esa reserva todavia no se ha hecho
        cancela = self.rng.random() < prob_cancelar(p_cancel, antel, d)
        cancelada_en = None
        if cancela:
            cancelada_en = creada + (inicio - creada) * self.rng.uniform(0.2, 0.95)
            if cancelada_en > self.ahora:
                cancela, cancelada_en = False, None
        self.filas.append({"cliente": cliente, "cancha": cancha, "franja": franja, "fecha": d,
                           "estado": "cancelada" if cancela else "confirmada",
                           "creada_en": creada, "cancelada_en": cancelada_en,
                           "antelacion_dias": round(antel, 2)})
        if not cancela:
            self.ocupados.add(clave)
        return not cancela

    def perfiles_demo(self, perfiles, hoy):
        """Primero juegan los perfiles demo: son los 'duenos' de sus franjas habituales.
        En el futuro solo se reserva su proximo partido habitual (ya hecho, con fecha de
        creacion en el pasado); el resto queda libre para que la IA lo recomiende."""
        proximo_hecho = set()
        for offset in range(-DIAS_HISTORIA, DIAS_FUTURO + 1):
            d = hoy + timedelta(days=offset)
            for p in perfiles:
                for dow, hora, ci, prob in p["habitos"]:
                    franja = self.por_hora.get(hora)
                    if d.weekday() != dow or not franja:
                        continue
                    pref = self.canchas[min(ci, len(self.canchas) - 1)]
                    inicio = datetime.combine(d, franja.HoraInicio)
                    if inicio > self.ahora:
                        self.protegidos.add((pref.CanchaId, franja.FranjaId, d))
                        if p["email"] in proximo_hecho:
                            continue
                        proximo_hecho.add(p["email"])
                        dias_que_faltan = (inicio - self.ahora).total_seconds() / 86400
                        self.intentar(p, pref, franja, d, p["antelacion"], 0.001,
                                      antel_min=dias_que_faltan + 0.2,
                                      antel_max=dias_que_faltan + 0.5 + p["antelacion"])
                        continue
                    if self.rng.random() > prob:
                        continue
                    for cancha in [pref] + [c for c in self.canchas if c is not pref]:
                        if (cancha.CanchaId, franja.FranjaId, d) not in self.ocupados:
                            self.intentar(p, cancha, franja, d, p["antelacion"], p["p_cancel"])
                            break
                if d < hoy and self.rng.random() < p["extra"]:  # reservas fuera de su patron
                    franja = self.rng.choice(self.franjas)
                    self.intentar(p, self.rng.choice(self.canchas), franja, d, p["antelacion"], p["p_cancel"])

    def multitud(self, clientes, hoy, fest):
        for offset in range(-DIAS_HISTORIA, DIAS_FUTURO + 1):
            d = hoy + timedelta(days=offset)
            fd = factor_fecha(d, fest)
            for i, cancha in enumerate(self.canchas):
                for franja in self.franjas:
                    clave = (cancha.CanchaId, franja.FranjaId, d)
                    if clave in self.ocupados or clave in self.protegidos:
                        continue
                    hora = franja.HoraInicio.hour
                    p = OCUPACION_BASE * fd * PESO_HORA.get(hora, 0.9) * PESO_CANCHA[min(i, 2)]
                    p = max(0.02, min(0.97, p))
                    intentos = 2 if self.rng.random() < 0.35 else 1  # re-toma de un cupo cancelado
                    for _ in range(intentos):
                        if self.rng.random() > p:
                            break
                        pesos = [afinidad(c, d, hora) for c in clientes]
                        c = self.rng.choices(clientes, weights=pesos, k=1)[0]
                        if self.intentar(c, cancha, franja, d, c["antelacion"], c["p_cancel"]):
                            break


def escribir_csv(filas):
    CSV_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fecha", "dia_semana", "hora_inicio", "cancha", "estado", "creada_en",
                    "cancelada_en", "antelacion_dias", "cliente", "cliente_email", "perfil_real"])
        for f in sorted(filas, key=lambda x: (x["fecha"], x["franja"].HoraInicio)):
            w.writerow([f["fecha"].isoformat(), f["fecha"].weekday(), f["franja"].HoraInicio.strftime("%H:%M"),
                        f["cancha"].Nombre, f["estado"], f["creada_en"].isoformat(timespec="minutes"),
                        f["cancelada_en"].isoformat(timespec="minutes") if f["cancelada_en"] else "",
                        f["antelacion_dias"], f["cliente"]["nombre"], f["cliente"]["email"],
                        f["cliente"]["perfil"]])


def borrar_sinteticos(db):
    ids = [u.UsuarioId for u in db.query(models.Usuario).filter(models.Usuario.Email.like("%" + DOMINIO))]
    q = db.query(models.Reserva).filter(models.Reserva.Celular.like(PREFIJO_CEL_DEMO + "%"))
    n_demo = q.delete(synchronize_session=False)
    if ids:
        db.query(models.Reserva).filter(models.Reserva.UsuarioId.in_(ids)).delete(synchronize_session=False)
        db.query(models.Usuario).filter(models.Usuario.UsuarioId.in_(ids)).delete(synchronize_session=False)
    db.commit()
    return len(ids), n_demo


def generar(reset=False, solo_csv=False, verbose=True):
    log = print if verbose else (lambda *a, **k: None)
    Base.metadata.create_all(bind=engine)
    seed()
    rng = random.Random(SEMILLA)
    db = SessionLocal()
    try:
        ya = db.query(models.Usuario).filter(models.Usuario.Email.like("%" + DOMINIO)).count()
        if ya and not reset and not solo_csv:
            log(f"Ya hay {ya} usuarios sinteticos. Usa --reset para regenerar.")
            return None
        if reset and not solo_csv:
            u, r = borrar_sinteticos(db)
            log(f"Borrados {u} usuarios sinteticos y {r} reservas demo de usuarios reales.")

        canchas = db.query(models.Cancha).filter(models.Cancha.Activa == True)\
            .order_by(models.Cancha.CanchaId).all()
        franjas = db.query(models.Franja).filter(models.Franja.Activa == True)\
            .order_by(models.Franja.HoraInicio).all()
        # Cupos ya tomados por reservas reales: el generador los respeta (indice unico).
        ocupados = {(r.CanchaId, r.FranjaId, r.Fecha) for r in
                    db.query(models.Reserva).filter(models.Reserva.Estado == "confirmada")}

        perfiles = [dict(p, celular=f"{PREFIJO_CEL_DEMO}{i:04d}") for i, p in enumerate(PERFILES_DEMO, 1)]
        multitud = crear_multitud(rng, franjas)
        hoy = date.today()
        fest = festivos(hoy.year) | festivos(hoy.year - 1) | festivos(hoy.year + 1)

        sim = Simulador(rng, canchas, franjas, ocupados)
        sim.perfiles_demo(perfiles, hoy)
        sim.multitud(multitud, hoy, fest)
        filas = sim.filas
        escribir_csv(filas)
        log(f"CSV: {CSV_SALIDA}  ({len(filas)} filas)")
        if solo_csv:
            return filas

        clave = hash_password(CLAVE_DEMO)  # un solo hash para todos (es lento)
        usuarios = {}
        for c in perfiles + multitud:
            u = db.query(models.Usuario).filter(models.Usuario.Email == c["email"]).first()
            if not u:
                u = models.Usuario(Nombre=c["nombre"], Email=c["email"], PasswordHash=clave, Rol="cliente")
                db.add(u)
            usuarios[c["email"]] = u
        db.flush()
        for f in filas:
            c = f["cliente"]
            db.add(models.Reserva(
                CanchaId=f["cancha"].CanchaId, FranjaId=f["franja"].FranjaId, Fecha=f["fecha"],
                UsuarioId=usuarios[c["email"]].UsuarioId, Estado=f["estado"],
                CreadaEn=f["creada_en"], CanceladaEn=f["cancelada_en"],
                NombreContacto=c["nombre"], Celular=c["celular"], CorreoContacto=c["email"]))
        db.commit()
        conf = sum(1 for f in filas if f["estado"] == "confirmada")
        log(f"Insertados {len(multitud)} clientes + {len(perfiles)} perfiles demo y {len(filas)} reservas "
            f"({conf} confirmadas, {len(filas) - conf} canceladas).")
        for p in perfiles:
            n = sum(1 for f in filas if f["cliente"] is p)
            log(f"  · {p['nombre']:<16} {p['perfil']:<24} {n:>3} reservas  ({p['email']})")
        return filas
    finally:
        db.close()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reset", action="store_true", help="borra los datos sinteticos antes de generar")
    ap.add_argument("--solo-csv", action="store_true", help="solo escribe el CSV, sin tocar la BD")
    args = ap.parse_args()
    generar(reset=args.reset, solo_csv=args.solo_csv)


if __name__ == "__main__":
    main()
