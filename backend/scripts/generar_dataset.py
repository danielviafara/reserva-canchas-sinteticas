"""Generador de un dataset FICTICIO de reservas para entrenar el modulo de IA.

Simula ~6 meses de historia de GolTime con patrones realistas de una cancha
sintetica en Colombia, para que los modelos tengan algo que aprender:

  * Demanda por dia de la semana: viernes y sabado son los mas fuertes, lunes el mas flojo.
  * Demanda por hora: 19:00 y 20:00 son la hora pico (salida del trabajo).
  * Efecto "quincena": los dias 14-16 y 29-31 (y 1) del mes sube la demanda.
  * Festivos colombianos (Ley Emiliani): bajan la demanda nocturna.
  * Diciembre: baja la demanda (vacaciones).
  * Cancha 1 es la favorita (mejor iluminacion, la mas cercana a la entrada).

Clientes por arquetipo (lo que el clustering deberia "descubrir" despues):
  * fiel:          juega casi cada semana el mismo dia y hora, reserva con antelacion, casi no cancela.
  * fin_de_semana: solo viernes/sabado/domingo.
  * ocasional:     reserva pocas veces, muchas veces el mismo dia.
  * impredecible:  reserva mucho con mucha antelacion y cancela a menudo.

La cancelacion depende de la antelacion, del arquetipo y del dia -> es lo que
aprende la regresion logistica del modulo de IA.

Uso (desde backend/ con el venv activo):
    python -m scripts.generar_dataset            # genera e inserta
    python -m scripts.generar_dataset --reset    # borra lo sintetico y regenera
    python -m scripts.generar_dataset --solo-csv # solo escribe el CSV, no toca la BD

Los usuarios sinteticos tienen correo @demo.goltime.co (contrasena: demo1234),
asi se pueden borrar sin tocar los datos reales.
"""
import argparse
import csv
import math
import random
import sys
from datetime import date, datetime, time, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.core.security import hash_password  # noqa: E402
from app.db import models  # noqa: E402
from app.db.session import Base, SessionLocal, engine  # noqa: E402

SEMILLA = 2026
DIAS_HISTORIA = 180
DIAS_FUTURO = 14
DOMINIO = "@demo.goltime.co"
CSV_SALIDA = Path(__file__).resolve().parents[2] / "database" / "dataset" / "reservas_sinteticas.csv"

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


def crear_clientes(rng: random.Random, franjas):
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
                "nombre": f"{nom} {ape}", "email": slug + DOMINIO, "arquetipo": arq,
                "actividad": actividad * rng.uniform(0.7, 1.3), "antelacion": antel,
                "p_cancel": pcancel, "dias_fav": dias_fav,
                "hora_fav": rng.choice([19, 20]) if arq == "fiel" else rng.choice(horas),
                "celular": "3" + "".join(str(rng.randint(0, 9)) for _ in range(9)),
            })
    return clientes


def afinidad(c, d: date, hora: int) -> float:
    a = c["actividad"]
    if d.weekday() in c["dias_fav"]:
        a *= 4.0 if c["arquetipo"] == "fiel" else 1.6
    elif c["arquetipo"] in ("fiel", "fin_de_semana"):
        a *= 0.08
    if hora == c["hora_fav"]:
        a *= 2.2
    return a


def prob_cancelar(c, antelacion_dias: float, d: date) -> float:
    z = math.log(c["p_cancel"] / (1 - c["p_cancel"]))
    z += 0.11 * antelacion_dias            # mas antelacion -> mas cancelacion
    z += 0.35 if d.weekday() == 6 else 0   # domingo: se cae mas el plan
    return 1 / (1 + math.exp(-z))


def simular(rng: random.Random, canchas, franjas, ocupados: set):
    hoy = date.today()
    ahora = datetime.now()
    fest = festivos(hoy.year) | festivos(hoy.year - 1) | festivos(hoy.year + 1)
    clientes = crear_clientes(rng, franjas)
    filas = []
    for offset in range(-DIAS_HISTORIA, DIAS_FUTURO + 1):
        d = hoy + timedelta(days=offset)
        fd = factor_fecha(d, fest)
        for i, cancha in enumerate(canchas):
            for franja in franjas:
                if (cancha.CanchaId, franja.FranjaId, d) in ocupados:
                    continue
                hora = franja.HoraInicio.hour
                p = OCUPACION_BASE * fd * PESO_HORA.get(hora, 0.9) * PESO_CANCHA[min(i, 2)]
                p = max(0.02, min(0.97, p))
                intentos = 2 if rng.random() < 0.35 else 1  # a veces alguien re-toma un cupo cancelado
                for _ in range(intentos):
                    if rng.random() > p:
                        break
                    pesos = [afinidad(c, d, hora) for c in clientes]
                    c = rng.choices(clientes, weights=pesos, k=1)[0]
                    antel = min(21.0, rng.expovariate(1 / max(0.3, c["antelacion"])))
                    inicio = datetime.combine(d, franja.HoraInicio)
                    creada = inicio - timedelta(days=antel, hours=rng.uniform(0, 6))
                    if creada > ahora:
                        break  # en el futuro: esa reserva todavia no se ha hecho
                    cancela = rng.random() < prob_cancelar(c, antel, d)
                    cancelada_en = None
                    if cancela:
                        cancelada_en = creada + (inicio - creada) * rng.uniform(0.2, 0.95)
                        if cancelada_en > ahora:
                            cancela, cancelada_en = False, None
                    filas.append({
                        "cliente": c, "cancha": cancha, "franja": franja, "fecha": d,
                        "estado": "cancelada" if cancela else "confirmada",
                        "creada_en": creada, "cancelada_en": cancelada_en,
                        "antelacion_dias": round(antel, 2),
                    })
                    if not cancela:
                        break  # el cupo queda ocupado
    return clientes, filas


def escribir_csv(filas):
    CSV_SALIDA.parent.mkdir(parents=True, exist_ok=True)
    with CSV_SALIDA.open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(["fecha", "dia_semana", "hora_inicio", "cancha", "estado", "creada_en",
                    "cancelada_en", "antelacion_dias", "cliente_email", "arquetipo_real"])
        for f in filas:
            w.writerow([f["fecha"].isoformat(), f["fecha"].weekday(), f["franja"].HoraInicio.strftime("%H:%M"),
                        f["cancha"].Nombre, f["estado"], f["creada_en"].isoformat(timespec="minutes"),
                        f["cancelada_en"].isoformat(timespec="minutes") if f["cancelada_en"] else "",
                        f["antelacion_dias"], f["cliente"]["email"], f["cliente"]["arquetipo"]])


def borrar_sinteticos(db):
    ids = [u.UsuarioId for u in db.query(models.Usuario).filter(models.Usuario.Email.like("%" + DOMINIO))]
    if ids:
        db.query(models.Reserva).filter(models.Reserva.UsuarioId.in_(ids)).delete(synchronize_session=False)
        db.query(models.Usuario).filter(models.Usuario.UsuarioId.in_(ids)).delete(synchronize_session=False)
        db.commit()
    return len(ids)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--reset", action="store_true", help="borra los datos sinteticos antes de generar")
    ap.add_argument("--solo-csv", action="store_true", help="solo escribe el CSV, sin tocar la BD")
    args = ap.parse_args()

    Base.metadata.create_all(bind=engine)
    rng = random.Random(SEMILLA)
    db = SessionLocal()
    try:
        ya = db.query(models.Usuario).filter(models.Usuario.Email.like("%" + DOMINIO)).count()
        if ya and not args.reset and not args.solo_csv:
            print(f"Ya hay {ya} usuarios sinteticos. Usa --reset para regenerar.")
            return
        if args.reset and not args.solo_csv:
            print(f"Borrados {borrar_sinteticos(db)} usuarios sinteticos y sus reservas.")

        canchas = db.query(models.Cancha).order_by(models.Cancha.CanchaId).all()
        franjas = db.query(models.Franja).filter(models.Franja.Activa == True)\
            .order_by(models.Franja.HoraInicio).all()
        # Cupos ya tomados por reservas reales: el generador los respeta (indice unico).
        ocupados = {(r.CanchaId, r.FranjaId, r.Fecha) for r in
                    db.query(models.Reserva).filter(models.Reserva.Estado == "confirmada")}

        clientes, filas = simular(rng, canchas, franjas, ocupados)
        escribir_csv(filas)
        print(f"CSV: {CSV_SALIDA}  ({len(filas)} filas)")
        if args.solo_csv:
            return

        clave = hash_password("demo1234")  # un solo hash para todos (es lento)
        por_email = {}
        for c in clientes:
            u = models.Usuario(Nombre=c["nombre"], Email=c["email"], PasswordHash=clave, Rol="cliente")
            db.add(u)
            por_email[c["email"]] = u
        db.flush()
        for f in filas:
            c = f["cliente"]
            db.add(models.Reserva(
                CanchaId=f["cancha"].CanchaId, FranjaId=f["franja"].FranjaId, Fecha=f["fecha"],
                UsuarioId=por_email[c["email"]].UsuarioId, Estado=f["estado"],
                CreadaEn=f["creada_en"], CanceladaEn=f["cancelada_en"],
                NombreContacto=c["nombre"], Celular=c["celular"], CorreoContacto=c["email"]))
        db.commit()
        conf = sum(1 for f in filas if f["estado"] == "confirmada")
        print(f"Insertados {len(clientes)} clientes y {len(filas)} reservas "
              f"({conf} confirmadas, {len(filas) - conf} canceladas).")
    finally:
        db.close()


if __name__ == "__main__":
    main()
