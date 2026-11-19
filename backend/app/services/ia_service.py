"""Modulo de inteligencia artificial de GolTime (Python puro, sin dependencias extra).

Aprende del historial de reservas que esta en la base de datos y ofrece cuatro cosas:

1. PREDICCION DE DEMANDA  ->  probabilidad de que una franja se ocupe.
   Para cada (dia de la semana, franja) se calcula la tasa historica de ocupacion,
   ponderando mas las semanas recientes (decaimiento exponencial, vida media 6 semanas)
   y con suavizado bayesiano (prior Beta) para no exagerar cuando hay pocos datos.
   Despues se ajusta por la popularidad relativa de cada cancha.

2. RIESGO DE CANCELACION  ->  regresion logistica entrenada con descenso de gradiente.
   Variables: antelacion de la reserva, fin de semana, domingo, hora pico y el
   historial de cancelaciones del cliente. Se valida con un corte temporal 80/20
   y se reporta exactitud y AUC.

3. SEGMENTACION DE CLIENTES  ->  K-means (k=4) sobre frecuencia, tasa de cancelacion,
   % de reservas en fin de semana, antelacion media y regularidad (cuanto repite dia+hora). Cada grupo se nombra segun su centroide.

4. RECOMENDACIONES E INSIGHTS  ->  sugiere al cliente franjas libres que encajan con sus
   habitos y genera hallazgos en lenguaje natural para el administrador.
"""
import math
import random
from collections import defaultdict
from datetime import date, datetime, timedelta

from sqlalchemy import func
from sqlalchemy.orm import Session

from app.db import models

DIAS = ["Lunes", "Martes", "Miércoles", "Jueves", "Viernes", "Sábado", "Domingo"]
VIDA_MEDIA_SEMANAS = 6.0
PRIOR_FUERZA = 3.0  # "reservas virtuales" del prior bayesiano

_cache = {"firma": None, "modelo": None}


# --------------------------------------------------------------------------- datos

def _cargar(db: Session):
    filas = (db.query(models.Reserva.ReservaId, models.Reserva.CanchaId, models.Reserva.FranjaId,
                      models.Reserva.Fecha, models.Reserva.UsuarioId, models.Reserva.Estado,
                      models.Reserva.CreadaEn)
             .all())
    franjas = {f.FranjaId: f for f in db.query(models.Franja).filter(models.Franja.Activa == True)}
    canchas = {c.CanchaId: c for c in db.query(models.Cancha).filter(models.Cancha.Activa == True)}
    return filas, franjas, canchas


def _firma(db: Session):
    """Cambia cada vez que se crea o cancela una reserva -> invalida la cache del modelo."""
    total = db.query(func.count(models.Reserva.ReservaId)).scalar()
    canceladas = db.query(func.count(models.Reserva.ReservaId))\
        .filter(models.Reserva.Estado == "cancelada").scalar()
    return (total, canceladas, date.today())


def _sigmoid(z):
    if z < -30:
        return 0.0
    if z > 30:
        return 1.0
    return 1 / (1 + math.exp(-z))


# --------------------------------------------------------------------------- 1. demanda

def _entrenar_demanda(filas, franjas, canchas, hoy):
    inicio = min((f.Fecha for f in filas), default=hoy)
    ocup = defaultdict(float)     # (dow, franja) -> ocupados ponderados
    total = defaultdict(float)    # (dow, franja) -> cupos ponderados
    ocup_cancha = defaultdict(int)
    confirmadas = {(f.CanchaId, f.FranjaId, f.Fecha) for f in filas if f.Estado == "confirmada"}
    n_canchas = max(1, len(canchas))

    d = inicio
    while d < hoy:
        semanas = (hoy - d).days / 7
        w = 0.5 ** (semanas / VIDA_MEDIA_SEMANAS)
        for fid in franjas:
            for cid in canchas:
                total[(d.weekday(), fid)] += w
                if (cid, fid, d) in confirmadas:
                    ocup[(d.weekday(), fid)] += w
                    ocup_cancha[cid] += 1
        d += timedelta(days=1)

    tot_global = sum(total.values()) or 1
    p_global = sum(ocup.values()) / tot_global
    tasa = {}
    for dow in range(7):
        for fid in franjas:
            k = (dow, fid)
            # Suavizado bayesiano: (exitos + a*p0) / (intentos + a)
            tasa[k] = (ocup[k] + PRIOR_FUERZA * p_global) / (total[k] + PRIOR_FUERZA)
    media_cancha = (sum(ocup_cancha.values()) / n_canchas) or 1
    factor_cancha = {cid: (ocup_cancha[cid] / media_cancha) if ocup_cancha else 1.0 for cid in canchas}
    return {"tasa": tasa, "factor_cancha": factor_cancha, "p_global": p_global}


def _prob_ocupacion(dem, cancha_id, franja_id, fecha):
    p = dem["tasa"].get((fecha.weekday(), franja_id), dem["p_global"])
    return max(0.01, min(0.99, p * dem["factor_cancha"].get(cancha_id, 1.0)))


def _nivel(p):
    if p >= 0.7:
        return "alta"
    if p >= 0.45:
        return "media"
    return "baja"


# --------------------------------------------------------------------------- 2. cancelacion

NOMBRES_VARIABLES = ["Antelación (días)", "Fin de semana", "Domingo", "Hora pico (19-21h)",
                     "Historial de cancelación del cliente"]


def _features(reserva, franja, hist_cancel):
    creada = reserva.CreadaEn or datetime.combine(reserva.Fecha, franja.HoraInicio)
    inicio = datetime.combine(reserva.Fecha, franja.HoraInicio)
    antel = max(0.0, (inicio - creada).total_seconds() / 86400)
    dow = reserva.Fecha.weekday()
    return [antel / 7.0, 1.0 if dow >= 4 else 0.0, 1.0 if dow == 6 else 0.0,
            1.0 if franja.HoraInicio.hour in (19, 20) else 0.0, hist_cancel]


def _dataset_cancelacion(filas, franjas):
    """Construye (x, y) en orden cronologico. El historial del cliente se calcula SOLO
    con reservas anteriores (sin mirar el futuro -> sin fuga de informacion)."""
    ordenadas = sorted((f for f in filas if f.FranjaId in franjas and f.CreadaEn),
                       key=lambda f: f.CreadaEn)
    previas = defaultdict(lambda: [0, 0])  # usuario -> [canceladas, total]
    X, y = [], []
    hoy = datetime.now()
    for r in ordenadas:
        fr = franjas[r.FranjaId]
        c, t = previas[r.UsuarioId]
        hist = (c + 0.15 * 2) / (t + 2)  # suavizado: cliente nuevo ~15 %
        inicio = datetime.combine(r.Fecha, fr.HoraInicio)
        if inicio < hoy:  # solo reservas cuyo desenlace ya se conoce
            X.append(_features(r, fr, hist))
            y.append(1 if r.Estado == "cancelada" else 0)
        previas[r.UsuarioId][1] += 1
        if r.Estado == "cancelada":
            previas[r.UsuarioId][0] += 1
    return X, y, previas


def _entrenar_logistica(X, y, epocas=400, lr=0.3, l2=0.001):
    n = len(X[0]) if X else len(NOMBRES_VARIABLES)
    w, b = [0.0] * n, 0.0
    m = len(X)
    for _ in range(epocas if m else 0):
        gw, gb = [0.0] * n, 0.0
        for xi, yi in zip(X, y):
            err = _sigmoid(b + sum(wj * xj for wj, xj in zip(w, xi))) - yi
            gb += err
            for j in range(n):
                gw[j] += err * xi[j]
        b -= lr * gb / m
        w = [wj - lr * (g / m + l2 * wj) for wj, g in zip(w, gw)]
    return w, b


def _auc(scores, y):
    pos = [s for s, t in zip(scores, y) if t == 1]
    neg = [s for s, t in zip(scores, y) if t == 0]
    if not pos or not neg:
        return None
    gana = sum((1.0 if p > q else 0.5 if p == q else 0.0) for p in pos for q in neg)
    return gana / (len(pos) * len(neg))


def _modelo_cancelacion(filas, franjas):
    X, y, previas = _dataset_cancelacion(filas, franjas)
    corte = int(len(X) * 0.8)
    w, b = _entrenar_logistica(X[:corte], y[:corte])
    test_x, test_y = X[corte:], y[corte:]
    scores = [_sigmoid(b + sum(a * c for a, c in zip(w, x))) for x in test_x]
    tasa_base = (sum(y[:corte]) / corte) if corte else 0.2
    umbral = 0.35
    aciertos = sum(1 for s, t in zip(scores, test_y) if (s >= umbral) == bool(t))
    mayoritaria = sum(1 for t in test_y if t == 0)
    return {
        "w": w, "b": b, "previas": previas,
        "metricas": {
            "registros_entrenamiento": corte, "registros_prueba": len(test_x),
            "exactitud": round(aciertos / len(test_x), 3) if test_x else None,
            "exactitud_base": round(mayoritaria / len(test_x), 3) if test_x else None,
            "auc": round(_auc(scores, test_y), 3) if test_x and _auc(scores, test_y) else None,
            "tasa_cancelacion": round(tasa_base, 3), "umbral": umbral,
        },
        "coeficientes": [{"variable": nv, "peso": round(wj, 3)} for nv, wj in zip(NOMBRES_VARIABLES, w)],
    }


def _riesgo(mc, reserva, franja):
    c, t = mc["previas"].get(reserva.UsuarioId, [0, 0])
    hist = (c + 0.3) / (t + 2)
    x = _features(reserva, franja, hist)
    return _sigmoid(mc["b"] + sum(a * v for a, v in zip(mc["w"], x)))


# --------------------------------------------------------------------------- 3. segmentacion

def _kmeans(puntos, k=4, iteraciones=50, semilla=7):
    rng = random.Random(semilla)
    if len(puntos) < k:
        return [0] * len(puntos), puntos[:]
    # k-means++: el primer centro al azar, los siguientes lejos de los ya elegidos
    centros = [rng.choice(puntos)]
    while len(centros) < k:
        d2 = [min(sum((a - b) ** 2 for a, b in zip(p, c)) for c in centros) for p in puntos]
        centros.append(rng.choices(puntos, weights=d2, k=1)[0])
    asign = [0] * len(puntos)
    for _ in range(iteraciones):
        asign = [min(range(k), key=lambda j: sum((a - b) ** 2 for a, b in zip(p, centros[j])))
                 for p in puntos]
        nuevos = []
        for j in range(k):
            miembros = [p for p, a in zip(puntos, asign) if a == j]
            nuevos.append([sum(v) / len(miembros) for v in zip(*miembros)] if miembros else centros[j])
        if nuevos == centros:
            break
        centros = nuevos
    return asign, centros


def _segmentar(filas, hoy):
    por_user = defaultdict(list)
    for f in filas:
        por_user[f.UsuarioId].append(f)
    meses = max(1.0, (hoy - min((f.Fecha for f in filas), default=hoy)).days / 30)
    ids, crudos = [], []
    for uid, rs in por_user.items():
        if len(rs) < 2:
            continue
        canc = sum(1 for r in rs if r.Estado == "cancelada") / len(rs)
        finde = sum(1 for r in rs if r.Fecha.weekday() >= 4) / len(rs)
        antel = sum(max(0, (r.Fecha - r.CreadaEn.date()).days) for r in rs if r.CreadaEn) / len(rs)
        # regularidad: que tanto repite su combinacion favorita de dia + franja
        combos = defaultdict(int)
        for r in rs:
            combos[(r.Fecha.weekday(), r.FranjaId)] += 1
        regular = max(combos.values()) / len(rs)
        ids.append(uid)
        crudos.append([len(rs) / meses, canc, finde, antel, regular])
    if not crudos:
        return []
    # normalizacion min-max para que ninguna variable domine por escala
    nf = len(crudos[0])
    mins = [min(c[i] for c in crudos) for i in range(nf)]
    maxs = [max(c[i] for c in crudos) for i in range(nf)]
    norm = [[(c[i] - mins[i]) / ((maxs[i] - mins[i]) or 1) for i in range(nf)] for c in crudos]
    asign, _ = _kmeans(norm)

    grupos = defaultdict(list)
    for a, c in zip(asign, crudos):
        grupos[a].append(c)
    resumen = []
    for j, cs in grupos.items():
        prom = [sum(v) / len(cs) for v in zip(*cs)]
        resumen.append({"clientes": len(cs), "frecuencia_mes": round(prom[0], 2),
                        "tasa_cancelacion": round(prom[1], 3), "pct_fin_de_semana": round(prom[2], 3),
                        "antelacion_dias": round(prom[3], 1), "regularidad": round(prom[4], 3)})
    # Nombrar cada grupo por su rasgo dominante (asignacion sin repetir)
    etiquetas = [
        ("En riesgo", "Cancelan con frecuencia: conviene pedir confirmación previa.",
         lambda g: g["tasa_cancelacion"]),
        ("Fieles", "Juegan casi cada semana y casi nunca cancelan: candidatos a plan mensual.",
         lambda g: g["regularidad"] - g["tasa_cancelacion"]),
        ("Fin de semana", "Concentran su juego de viernes a domingo.",
         lambda g: g["pct_fin_de_semana"]),
        ("Ocasionales", "Reservan pocas veces y con poca antelación: responden bien a promociones.",
         lambda g: -g["frecuencia_mes"]),
    ]
    libres = list(range(len(resumen)))
    for nombre, desc, score in etiquetas:
        if not libres:
            break
        mejor = max(libres, key=lambda i: score(resumen[i]))
        resumen[mejor].update({"nombre": nombre, "descripcion": desc})
        libres.remove(mejor)
    for i in libres:
        resumen[i].update({"nombre": f"Grupo {i + 1}", "descripcion": ""})
    return sorted(resumen, key=lambda g: -g["clientes"])


# --------------------------------------------------------------------------- orquestacion

def _modelo(db: Session):
    firma = _firma(db)
    if _cache["firma"] == firma:
        return _cache["modelo"]
    filas, franjas, canchas = _cargar(db)
    hoy = date.today()
    modelo = {
        "filas": filas, "franjas": franjas, "canchas": canchas, "hoy": hoy,
        "demanda": _entrenar_demanda(filas, franjas, canchas, hoy),
        "cancelacion": _modelo_cancelacion(filas, franjas),
        "segmentos": _segmentar(filas, hoy),
        "entrenado_en": datetime.now().isoformat(timespec="seconds"),
    }
    _cache.update(firma=firma, modelo=modelo)
    return modelo


def _hhmm(t):
    return t.strftime("%H:%M")


def demanda_dia(db: Session, cancha_id: int, fecha: date):
    """Probabilidad de ocupacion estimada para cada franja de una cancha en una fecha."""
    m = _modelo(db)
    salida = []
    for fid, fr in sorted(m["franjas"].items(), key=lambda kv: kv[1].HoraInicio):
        p = _prob_ocupacion(m["demanda"], cancha_id, fid, fecha)
        salida.append({"franja_id": fid, "hora_inicio": _hhmm(fr.HoraInicio),
                       "probabilidad": round(p, 3), "nivel": _nivel(p)})
    return salida


def recomendaciones(db: Session, usuario_id: int, dias: int = 7, n: int = 3):
    """Franjas libres de los proximos dias que encajan con los habitos del cliente.

    puntaje = afinidad con su historial (dia y hora que mas juega)
              x  (1 - probabilidad de ocupacion)^0.5  -> premia cupos 'faciles' de conseguir
    Para un cliente sin historial se usan los habitos globales."""
    m = _modelo(db)
    propias = [f for f in m["filas"] if f.UsuarioId == usuario_id and f.Estado == "confirmada"]
    pref_dia, pref_franja = defaultdict(float), defaultdict(float)
    base = propias if len(propias) >= 2 else [f for f in m["filas"] if f.Estado == "confirmada"]
    for f in base:
        pref_dia[f.Fecha.weekday()] += 1
        pref_franja[f.FranjaId] += 1
    td, tf = sum(pref_dia.values()) or 1, sum(pref_franja.values()) or 1

    confirmadas = {(f.CanchaId, f.FranjaId, f.Fecha) for f in m["filas"] if f.Estado == "confirmada"}
    ahora = datetime.now()
    candidatos = []
    for off in range(0, dias + 1):
        d = m["hoy"] + timedelta(days=off)
        for fid, fr in m["franjas"].items():
            if datetime.combine(d, fr.HoraInicio) <= ahora:
                continue
            for cid, ca in m["canchas"].items():
                if (cid, fid, d) in confirmadas:
                    continue
                p = _prob_ocupacion(m["demanda"], cid, fid, d)
                afin = (0.3 + pref_dia[d.weekday()] / td * 7) * (0.3 + pref_franja[fid] / tf * len(m["franjas"]))
                puntaje = afin * (1 - p) ** 0.5
                candidatos.append((puntaje, d, fid, fr, cid, ca, p))
    candidatos.sort(key=lambda c: -c[0])

    salida, vistos = [], set()
    for puntaje, d, fid, fr, cid, ca, p in candidatos:
        if (d, fid) in vistos:  # una sola cancha por fecha/hora para variar
            continue
        vistos.add((d, fid))
        if len(propias) >= 2:
            motivo = (f"Sueles jugar los {DIAS[d.weekday()].lower()}" if pref_dia[d.weekday()] / td >= 0.2
                      else "Es tu horario habitual" if pref_franja[fid] / tf >= 0.3
                      else "Un buen cupo para probar otro día")
        else:
            motivo = "Horario muy solicitado por la comunidad"
        if p >= 0.7:
            motivo += ". Se llena rápido: resérvala ya."
        else:
            motivo += f". Aún tienes {100 - round(p * 100)} % de probabilidad de encontrarla libre."
        salida.append({"fecha": d.isoformat(), "dia": DIAS[d.weekday()], "franja_id": fid,
                       "hora_inicio": _hhmm(fr.HoraInicio), "hora_fin": _hhmm(fr.HoraFin),
                       "cancha_id": cid, "cancha": ca.Nombre, "probabilidad": round(p, 3),
                       "nivel": _nivel(p), "motivo": motivo,
                       "afinidad": round(min(1.0, puntaje / (candidatos[0][0] or 1)), 2)})
        if len(salida) >= n:
            break
    return {"personalizado": len(propias) >= 2, "items": salida}


def resumen_admin(db: Session):
    """Tablero de IA para el administrador."""
    m = _modelo(db)
    filas, franjas, canchas, hoy = m["filas"], m["franjas"], m["canchas"], m["hoy"]
    franjas_ord = sorted(franjas.items(), key=lambda kv: kv[1].HoraInicio)
    pasadas = [f for f in filas if f.Fecha < hoy]
    conf = [f for f in pasadas if f.Estado == "confirmada"]
    dias_hist = len({f.Fecha for f in pasadas}) or 1
    cupos = dias_hist * len(franjas) * max(1, len(canchas))

    # Mapa de calor real (ultimas 8 semanas) vs prediccion
    desde = hoy - timedelta(weeks=8)
    real = defaultdict(int)
    for f in conf:
        if f.Fecha >= desde:
            real[(f.Fecha.weekday(), f.FranjaId)] += 1
    cupos_celda = 8 * max(1, len(canchas))
    heat = [{"dia": DIAS[dow], "dow": dow, "celdas": [
        {"hora": _hhmm(fr.HoraInicio), "real": round(real[(dow, fid)] / cupos_celda, 3),
         "prediccion": round(m["demanda"]["tasa"].get((dow, fid), 0), 3)}
        for fid, fr in franjas_ord]} for dow in range(7)]

    # Pronostico proximos 7 dias: ocupacion esperada vs ya reservada
    confirmadas = {(f.CanchaId, f.FranjaId, f.Fecha) for f in filas if f.Estado == "confirmada"}
    pronostico = []
    for off in range(7):
        d = hoy + timedelta(days=off)
        esperado = sum(_prob_ocupacion(m["demanda"], cid, fid, d) for cid in canchas for fid in franjas)
        ya = sum(1 for cid in canchas for fid in franjas if (cid, fid, d) in confirmadas)
        total = len(canchas) * len(franjas)
        pronostico.append({"fecha": d.isoformat(), "dia": DIAS[d.weekday()][:3],
                           "esperado": round(esperado / total, 3), "reservado": round(ya / total, 3),
                           "cupos": total})

    # Reservas proximas con mayor riesgo de cancelacion
    mc = m["cancelacion"]
    nombres = {u.UsuarioId: u.Nombre for u in db.query(models.Usuario.UsuarioId, models.Usuario.Nombre)}
    proximas = []
    for f in filas:
        if f.Estado != "confirmada" or f.Fecha < hoy or f.Fecha > hoy + timedelta(days=7):
            continue
        fr = franjas.get(f.FranjaId)
        if not fr or f.CanchaId not in canchas or datetime.combine(f.Fecha, fr.HoraInicio) <= datetime.now():
            continue
        proximas.append({"reserva_id": f.ReservaId, "fecha": f.Fecha.isoformat(), "dia": DIAS[f.Fecha.weekday()],
                         "hora": _hhmm(fr.HoraInicio), "cancha": canchas[f.CanchaId].Nombre,
                         "cliente": nombres.get(f.UsuarioId, "—"), "riesgo": round(_riesgo(mc, f, fr), 3)})
    proximas.sort(key=lambda r: -r["riesgo"])

    # Insights en lenguaje natural
    celdas = [(c["prediccion"], h["dia"], c["hora"]) for h in heat for c in h["celdas"]]
    pico, valle = max(celdas), min(celdas)
    por_dia = sorted(((sum(c["prediccion"] for c in h["celdas"]) / max(1, len(h["celdas"])), h["dia"])
                      for h in heat), reverse=True)
    top_cancha = max(m["demanda"]["factor_cancha"].items(), key=lambda kv: kv[1], default=(None, 1))
    coef = sorted(mc["coeficientes"], key=lambda c: -abs(c["peso"]))
    tasa_canc = sum(1 for f in pasadas if f.Estado == "cancelada") / (len(pasadas) or 1)
    insights = [
        {"icono": "flame", "titulo": f"Hora pico: {pico[1]} {pico[2]}",
         "texto": f"Se ocupa el {pico[0] * 100:.0f} % de las veces. Es candidata a tarifa premium."},
        {"icono": "trend", "titulo": f"{por_dia[0][1]} es el día más fuerte",
         "texto": f"Ocupación esperada de {por_dia[0][0] * 100:.0f} %, frente a {por_dia[-1][0] * 100:.0f} % "
                  f"del {por_dia[-1][1].lower()}."},
        {"icono": "spark", "titulo": f"Oportunidad: {valle[1]} {valle[2]}",
         "texto": f"Solo {valle[0] * 100:.0f} % de ocupación. Una promoción 2x1 podría llenar ese cupo."},
        {"icono": "pitch", "titulo": f"{canchas[top_cancha[0]].Nombre if top_cancha[0] in canchas else '—'} es la favorita",
         "texto": f"Recibe {(top_cancha[1] - 1) * 100:+.0f} % de reservas frente al promedio de canchas."},
        {"icono": "x", "titulo": f"{tasa_canc * 100:.0f} % de cancelaciones",
         "texto": f"La variable que más pesa en el riesgo es «{coef[0]['variable']}»."
                  if coef else "Sin datos suficientes."},
    ]

    return {
        "entrenado_en": m["entrenado_en"],
        "dataset": {"reservas": len(filas), "clientes": len({f.UsuarioId for f in filas}),
                    "desde": min((f.Fecha for f in filas), default=hoy).isoformat(),
                    "hasta": max((f.Fecha for f in filas), default=hoy).isoformat()},
        "kpis": {"ocupacion": round(len(conf) / cupos, 3), "tasa_cancelacion": round(tasa_canc, 3),
                 "reservas_mes": sum(1 for f in conf if f.Fecha >= hoy - timedelta(days=30)),
                 "ocupacion_7d_esperada": round(sum(p["esperado"] for p in pronostico) / 7, 3)},
        "heatmap": heat, "pronostico": pronostico, "segmentos": m["segmentos"],
        "cancelacion": {"metricas": mc["metricas"], "coeficientes": mc["coeficientes"],
                        "en_riesgo": proximas[:8]},
        "insights": insights,
    }
