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
DIAS_PLURAL = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábados", "domingos"]
MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]
EMAILS_DEMO = {"daniel@correo.com", "laura@demo.goltime.co", "andres@demo.goltime.co",
               "camila@demo.goltime.co", "julian@demo.goltime.co"}
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
    umbral = 0.5
    aciertos = sum(1 for s, t in zip(scores, test_y) if (s >= umbral) == bool(t))
    mayoritaria = sum(1 for t in test_y if t == 0)
    # "Lift": de las reservas que el modelo considera mas riesgosas (20 % superior),
    # que proporcion se cancelo de verdad, frente a la tasa promedio del conjunto de prueba.
    ranking = sorted(zip(scores, test_y), key=lambda st: -st[0])
    top = ranking[:max(1, len(ranking) // 5)]
    tasa_top = sum(t for _, t in top) / len(top) if top else 0
    tasa_test = sum(test_y) / len(test_y) if test_y else 0
    return {
        "w": w, "b": b, "previas": previas,
        "metricas": {
            "registros_entrenamiento": corte, "registros_prueba": len(test_x),
            "exactitud": round(aciertos / len(test_x), 3) if test_x else None,
            "exactitud_base": round(mayoritaria / len(test_x), 3) if test_x else None,
            "auc": round(_auc(scores, test_y), 3) if test_x and _auc(scores, test_y) else None,
            "tasa_cancelacion": round(tasa_base, 3), "umbral": umbral,
            "tasa_top20": round(tasa_top, 3), "tasa_prueba": round(tasa_test, 3),
            "lift": round(tasa_top / tasa_test, 2) if tasa_test else None,
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


NOMBRES_SEGMENTO = {
    "En riesgo": "Cancelan con frecuencia: conviene pedir confirmación previa.",
    "Fieles": "Juegan casi cada semana en el mismo horario y casi nunca cancelan: candidatos a plan mensual.",
    "Fin de semana": "Concentran su juego de viernes a domingo.",
    "Ocasionales": "Reservan pocas veces y con poca antelación: responden bien a promociones.",
}


def _segmentar(filas, hoy):
    """K-means sobre el comportamiento de cada cliente.

    Las tasas de cada cliente se SUAVIZAN hacia el promedio general (prior de 3 reservas):
    con 3 reservas una sola cancelacion seria un 33 %, lo que meteria mucho ruido.
    Despues se escala cada variable con percentiles, se pondera y se corre K-means con
    varios reinicios. Por ultimo cada grupo recibe el nombre que mejor describe su
    centroide, probando todas las asignaciones posibles (no de forma voraz)."""
    from itertools import permutations
    por_user = defaultdict(list)
    for f in filas:
        por_user[f.UsuarioId].append(f)
    meses = max(1.0, (hoy - min((f.Fecha for f in filas), default=hoy)).days / 30)
    todas = [f for f in filas]
    g_canc = sum(1 for f in todas if f.Estado == "cancelada") / (len(todas) or 1)
    g_finde = sum(1 for f in todas if f.Fecha.weekday() >= 4) / (len(todas) or 1)
    k0 = 3.0  # fuerza del prior
    ids, crudos = [], []
    for uid, rs in por_user.items():
        if len(rs) < 3:
            continue
        n = len(rs)
        canc = (sum(1 for r in rs if r.Estado == "cancelada") + k0 * g_canc) / (n + k0)
        finde = (sum(1 for r in rs if r.Fecha.weekday() >= 4) + k0 * g_finde) / (n + k0)
        antel = sum(max(0, (r.Fecha - r.CreadaEn.date()).days) for r in rs if r.CreadaEn) / n
        combos = defaultdict(int)
        for r in rs:
            combos[(r.Fecha.weekday(), r.FranjaId)] += 1
        regular = max(combos.values()) / (n + k0)  # regularidad: cuanto repite dia + franja
        ids.append(uid)
        crudos.append([n / meses, canc, finde, antel, regular])
    if len(crudos) < 4:
        return {"resumen": [], "por_usuario": {}, "promedios": {}}

    nf = len(crudos[0])
    pesos = [0.8, 1.5, 1.2, 0.5, 1.3]  # frecuencia, cancelacion, fin de semana, antelacion, regularidad

    def pct(vals, q):
        v = sorted(vals)
        return v[min(len(v) - 1, int(q * (len(v) - 1)))]
    lo = [pct([c[i] for c in crudos], 0.05) for i in range(nf)]
    hi = [pct([c[i] for c in crudos], 0.95) for i in range(nf)]
    esc = lambda c: [min(1.0, max(0.0, (c[i] - lo[i]) / ((hi[i] - lo[i]) or 1))) for i in range(nf)]  # noqa: E731
    norm = [[pesos[i] * v for i, v in enumerate(esc(c))] for c in crudos]
    mejor = None
    for semilla in range(16):
        asign, centros = _kmeans(norm, semilla=semilla)
        inercia = sum(sum((a - b) ** 2 for a, b in zip(p, centros[g])) for p, g in zip(norm, asign))
        if mejor is None or inercia < mejor[0]:
            mejor = (inercia, asign)
    asign = mejor[1]

    grupos = defaultdict(list)
    for a, c in zip(asign, crudos):
        grupos[a].append(c)
    claves = list(grupos)
    cent = {j: esc([sum(v) / len(grupos[j]) for v in zip(*grupos[j])]) for j in claves}
    # puntaje de cada nombre para un centroide (variables escaladas 0-1)
    afin = {
        "En riesgo": lambda c: 2 * c[1] + 0.3 * c[3],
        "Fieles": lambda c: 1.5 * c[4] + 0.5 * c[0] - c[1] - 0.6 * c[2],
        "Fin de semana": lambda c: 2 * c[2] - 0.5 * c[1],
        "Ocasionales": lambda c: -1.5 * c[0] - c[4],
    }
    nombres = list(afin)
    mejor_perm = max(permutations(nombres, len(claves)),
                     key=lambda perm: sum(afin[nm](cent[j]) for nm, j in zip(perm, claves)))
    nombre_de = dict(zip(claves, mejor_perm))

    resumen = []
    for j in claves:
        prom = [sum(v) / len(grupos[j]) for v in zip(*grupos[j])]
        resumen.append({"nombre": nombre_de[j], "descripcion": NOMBRES_SEGMENTO[nombre_de[j]],
                        "clientes": len(grupos[j]), "frecuencia_mes": round(prom[0], 2),
                        "tasa_cancelacion": round(prom[1], 3), "pct_fin_de_semana": round(prom[2], 3),
                        "antelacion_dias": round(prom[3], 1), "regularidad": round(prom[4], 3)})
    por_usuario = {uid: nombre_de[a] for uid, a in zip(ids, asign)}
    promedios = {"frecuencia_mes": round(sum(c[0] for c in crudos) / len(crudos), 2),
                 "tasa_cancelacion": round(g_canc, 3),
                 "regularidad": round(sum(c[4] for c in crudos) / len(crudos), 3)}
    return {"resumen": sorted(resumen, key=lambda g: -g["clientes"]),
            "por_usuario": por_usuario, "promedios": promedios}


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


def _habitos(filas_usuario):
    """Cuenta en que dia, franja, cancha y combinacion dia+franja juega un cliente."""
    dia, franja, cancha, combo = defaultdict(int), defaultdict(int), defaultdict(int), defaultdict(int)
    for f in filas_usuario:
        dia[f.Fecha.weekday()] += 1
        franja[f.FranjaId] += 1
        cancha[f.CanchaId] += 1
        combo[(f.Fecha.weekday(), f.FranjaId)] += 1
    return {"dia": dia, "franja": franja, "cancha": cancha, "combo": combo, "n": len(filas_usuario)}


def _recomendar(m, usuario_id, dias=7, n=3):
    """Franjas libres de los proximos dias que encajan con los habitos del cliente.

    coincidencia = 0.6 x (su combinacion dia+hora) + 0.25 x (su dia) + 0.15 x (su hora),
                   cada parte normalizada contra su favorita (1 = su favorita).
    puntaje      = (0.15 + coincidencia) x preferencia de cancha x sqrt(1 - demanda)
    La raiz de (1 - demanda) premia los cupos que todavia se pueden conseguir.
    Un cliente con menos de 3 reservas recibe los habitos de toda la comunidad."""
    propias = [f for f in m["filas"] if f.UsuarioId == usuario_id and f.Estado == "confirmada"]
    personalizado = len(propias) >= 3
    h = _habitos(propias if personalizado else [f for f in m["filas"] if f.Estado == "confirmada"])
    mx = {k: (max(h[k].values()) if h[k] else 1) for k in ("dia", "franja", "cancha", "combo")}

    confirmadas = {(f.CanchaId, f.FranjaId, f.Fecha) for f in m["filas"] if f.Estado == "confirmada"}
    ya_juega = {(f.FranjaId, f.Fecha) for f in propias}
    ahora = datetime.now()
    candidatos = []
    for off in range(0, dias + 1):
        d = m["hoy"] + timedelta(days=off)
        dow = d.weekday()
        for fid, fr in m["franjas"].items():
            if datetime.combine(d, fr.HoraInicio) <= ahora or (fid, d) in ya_juega:
                continue
            coinc = (0.6 * h["combo"][(dow, fid)] / mx["combo"] + 0.25 * h["dia"][dow] / mx["dia"]
                     + 0.15 * h["franja"][fid] / mx["franja"])
            for cid, ca in m["canchas"].items():
                if (cid, fid, d) in confirmadas:
                    continue
                p = _prob_ocupacion(m["demanda"], cid, fid, d)
                pref_c = 0.6 + 0.4 * h["cancha"][cid] / mx["cancha"]
                candidatos.append(((0.15 + coinc) * pref_c * (1 - p) ** 0.5, coinc, d, fid, fr, cid, ca, p))
    candidatos.sort(key=lambda c: -c[0])

    favorita_cancha = max(h["cancha"], key=h["cancha"].get) if h["cancha"] else None
    salida, vistos = [], set()
    for puntaje, coinc, d, fid, fr, cid, ca, p in candidatos:
        if (d, fid) in vistos:  # una sola cancha por fecha/hora
            continue
        vistos.add((d, fid))
        dow = d.weekday()
        if not personalizado:
            motivo = "Horario muy solicitado por la comunidad"
        elif h["combo"][(dow, fid)] >= 3 and h["combo"][(dow, fid)] / max(1, h["n"]) >= 0.12:
            motivo = f"Tu clásico: {DIAS_PLURAL[dow]} a las {_hhmm(fr.HoraInicio)}"
        elif h["dia"][dow] / max(1, h["n"]) >= 0.2:
            motivo = f"Sueles jugar los {DIAS_PLURAL[dow]}"
        elif h["franja"][fid] / max(1, h["n"]) >= 0.3:
            motivo = f"Es tu hora habitual ({_hhmm(fr.HoraInicio)})"
        else:
            motivo = "Un buen cupo para variar tu rutina"
        if personalizado and cid == favorita_cancha:
            motivo += f" en {ca.Nombre}, tu favorita"
        motivo += (". Se llena rápido: resérvala ya." if p >= 0.7
                   else f". {100 - round(p * 100)} % de probabilidad de encontrarla libre.")
        salida.append({"fecha": d.isoformat(), "dia": DIAS[dow], "franja_id": fid,
                       "hora_inicio": _hhmm(fr.HoraInicio), "hora_fin": _hhmm(fr.HoraFin),
                       "cancha_id": cid, "cancha": ca.Nombre, "probabilidad": round(p, 3),
                       "nivel": _nivel(p), "motivo": motivo, "afinidad": round(min(1.0, coinc), 2)})
        if len(salida) >= n:
            break
    return {"personalizado": personalizado, "items": salida}


def recomendaciones(db: Session, usuario_id: int, dias: int = 7, n: int = 3):
    return _recomendar(_modelo(db), usuario_id, dias, n)


SEGMENTO_INFO = {
    "Fieles": "Juegas casi cada semana, en tu mismo horario, y casi nunca cancelas.",
    "Fin de semana": "Tu fútbol vive de viernes a domingo.",
    "En riesgo": "Reservas mucho y con antelación, pero cancelas con frecuencia.",
    "Ocasionales": "Juegas de vez en cuando y sueles reservar sobre la marcha.",
    "Nuevo": "Aún tenemos pocas reservas tuyas para reconocer tu patrón.",
}


def _perfil(m, usuario_id, usuario=None):
    hoy, ahora = m["hoy"], datetime.now()
    franjas, canchas = m["franjas"], m["canchas"]
    todas = [f for f in m["filas"] if f.UsuarioId == usuario_id and f.FranjaId in franjas]
    conf = [f for f in todas if f.Estado == "confirmada"]
    inicio = lambda f: datetime.combine(f.Fecha, franjas[f.FranjaId].HoraInicio)
    jugadas = [f for f in conf if inicio(f) < ahora]
    proximas = sorted((f for f in conf if inicio(f) >= ahora), key=inicio)
    canceladas = [f for f in todas if f.Estado == "cancelada"]
    meses = max(1.0, (hoy - min((f.Fecha for f in m["filas"]), default=hoy)).days / 30)
    h = _habitos(conf)
    seg = m["segmentos"]["por_usuario"].get(usuario_id, "Nuevo")
    franjas_ord = sorted(franjas.items(), key=lambda kv: kv[1].HoraInicio)

    combos = sorted(h["combo"].items(), key=lambda kv: -kv[1])[:3]
    top = [{"dia": DIAS[d], "hora": _hhmm(franjas[fid].HoraInicio), "veces": v,
            "porcentaje": round(v / max(1, h["n"]), 3)} for (d, fid), v in combos]
    fav_dia = max(h["dia"], key=h["dia"].get) if h["dia"] else None
    fav_franja = max(h["franja"], key=h["franja"].get) if h["franja"] else None
    fav_cancha = max(h["cancha"], key=h["cancha"].get) if h["cancha"] else None
    antel = [max(0.0, (inicio(f) - f.CreadaEn).total_seconds() / 86400) for f in todas if f.CreadaEn]
    tasa_c = len(canceladas) / len(todas) if todas else 0

    # Frase del patron detectado
    if h["n"] >= 3 and top and top[0]["veces"] < 3:
        patron = (f"No tienes un día fijo: has jugado {len(jugadas)} veces en {round(meses)} meses, "
                  f"en días y horas distintos. ")
        patron += "Casi nunca cancelas." if tasa_c < 0.1 else f"Cancelas el {round(tasa_c * 100)} % de tus reservas."
    elif h["n"] >= 3:
        claves = [t for t in top if t["porcentaje"] >= 0.12 and t["veces"] >= 3][:2] or top[:1]
        cuando = " y ".join(f"{DIAS_PLURAL[DIAS.index(t['dia'])]} a las {t['hora']}" for t in claves)
        patron = (f"Juegas sobre todo los {cuando}"
                  f"{', casi siempre en ' + canchas[fav_cancha].Nombre if fav_cancha in canchas and h['cancha'][fav_cancha] / h['n'] >= 0.5 else ''}. ")
        patron += ("Casi nunca cancelas." if tasa_c < 0.1 else
                   f"Cancelas el {round(tasa_c * 100)} % de tus reservas." if tasa_c >= 0.25 else
                   "Cancelas poco.")
    else:
        patron = "Aún no hay suficientes reservas para reconocer un patrón. Juega un par de veces más."

    # Ultimos 6 meses
    mensual = []
    y, mth = hoy.year, hoy.month
    for k in range(5, -1, -1):
        mm, yy = mth - k, y
        while mm <= 0:
            mm, yy = mm + 12, yy - 1
        mensual.append({"mes": MESES[mm - 1], "jugadas": sum(1 for f in jugadas if (f.Fecha.year, f.Fecha.month) == (yy, mm)),
                        "canceladas": sum(1 for f in canceladas if (f.Fecha.year, f.Fecha.month) == (yy, mm))})

    heat = [{"dia": DIAS[d], "celdas": [{"hora": _hhmm(fr.HoraInicio), "veces": h["combo"][(d, fid)]}
                                         for fid, fr in franjas_ord]} for d in range(7)]

    prox = None
    if proximas:
        f = proximas[0]
        prox = {"fecha": f.Fecha.isoformat(), "dia": DIAS[f.Fecha.weekday()], "hora": _hhmm(franjas[f.FranjaId].HoraInicio),
                "cancha": canchas[f.CanchaId].Nombre if f.CanchaId in canchas else "—",
                "riesgo": round(_riesgo(m["cancelacion"], f, franjas[f.FranjaId]), 3)}

    return {
        "usuario_id": usuario_id,
        "nombre": usuario.Nombre if usuario else None, "email": usuario.Email if usuario else None,
        "segmento": {"nombre": seg, "descripcion": SEGMENTO_INFO.get(seg, "")},
        "patron": patron,
        "stats": {"reservas": len(todas), "jugadas": len(jugadas), "proximas": len(proximas),
                  "canceladas": len(canceladas), "tasa_cancelacion": round(tasa_c, 3),
                  "frecuencia_mes": round(len(todas) / meses, 2),
                  "antelacion_dias": round(sum(antel) / len(antel), 1) if antel else 0,
                  "regularidad": round(top[0]["veces"] / h["n"], 3) if top else 0},
        "comunidad": m["segmentos"]["promedios"],
        "favoritos": {"dia": DIAS[fav_dia] if fav_dia is not None else None,
                      "hora": _hhmm(franjas[fav_franja].HoraInicio) if fav_franja else None,
                      "cancha": canchas[fav_cancha].Nombre if fav_cancha in canchas else None,
                      "combos": top},
        "heatmap": heat, "mensual": mensual, "proxima": prox,
        "recomendaciones": _recomendar(m, usuario_id),
    }


def mi_perfil(db: Session, usuario_id: int):
    return _perfil(_modelo(db), usuario_id, db.get(models.Usuario, usuario_id))


def perfil_cliente(db: Session, usuario_id: int):
    u = db.get(models.Usuario, usuario_id)
    if not u:
        return None
    return _perfil(_modelo(db), usuario_id, u)


def clientes(db: Session):
    """Tabla de clientes con su segmento y su patron principal (para el admin)."""
    m = _modelo(db)
    franjas = m["franjas"]
    por_user = defaultdict(list)
    for f in m["filas"]:
        if f.FranjaId in franjas:
            por_user[f.UsuarioId].append(f)
    usuarios = {u.UsuarioId: u for u in db.query(models.Usuario).filter(models.Usuario.Rol == "cliente")}
    meses = max(1.0, (m["hoy"] - min((f.Fecha for f in m["filas"]), default=m["hoy"])).days / 30)
    salida = []
    for uid, u in usuarios.items():
        rs = por_user.get(uid, [])
        conf = [f for f in rs if f.Estado == "confirmada"]
        h = _habitos(conf)
        top = max(h["combo"].items(), key=lambda kv: kv[1]) if h["combo"] else None
        salida.append({
            "usuario_id": uid, "nombre": u.Nombre, "email": u.Email,
            "demo": u.Email in EMAILS_DEMO,
            "segmento": m["segmentos"]["por_usuario"].get(uid, "Nuevo"),
            "reservas": len(rs), "frecuencia_mes": round(len(rs) / meses, 2),
            "tasa_cancelacion": round(sum(1 for f in rs if f.Estado == "cancelada") / len(rs), 3) if rs else 0,
            "patron": f"{DIAS[top[0][0]][:3]} {_hhmm(franjas[top[0][1]].HoraInicio)}" if top else "—",
            "regularidad": round(top[1] / h["n"], 3) if top else 0,
            "ultima": max(f.Fecha for f in rs).isoformat() if rs else None,
        })
    return sorted(salida, key=lambda c: (not c["demo"], -c["reservas"]))


COLUMNAS_DATASET = [
    ("reserva_id", "Identificador de la reserva"),
    ("fecha", "Día del partido (AAAA-MM-DD)"),
    ("dia_semana", "0 = lunes … 6 = domingo"),
    ("hora_inicio", "Inicio de la franja"),
    ("cancha", "Cancha reservada"),
    ("estado", "confirmada | cancelada"),
    ("creada_en", "Cuándo se hizo la reserva"),
    ("antelacion_dias", "Días entre la reserva y el partido (variable del modelo de cancelación)"),
    ("fin_de_semana", "1 si es viernes, sábado o domingo"),
    ("cliente", "Nombre del cliente"),
    ("segmento_ia", "Grupo asignado por K-means"),
]


def _filas_dataset(db: Session, m):
    franjas, canchas = m["franjas"], m["canchas"]
    nombres = {u.UsuarioId: u.Nombre for u in db.query(models.Usuario.UsuarioId, models.Usuario.Nombre)}
    for f in sorted(m["filas"], key=lambda r: (r.Fecha, r.ReservaId), reverse=True):
        fr = franjas.get(f.FranjaId)
        if not fr:
            continue
        ini = datetime.combine(f.Fecha, fr.HoraInicio)
        antel = max(0.0, (ini - f.CreadaEn).total_seconds() / 86400) if f.CreadaEn else None
        yield {"reserva_id": f.ReservaId, "fecha": f.Fecha.isoformat(), "dia_semana": f.Fecha.weekday(),
               "hora_inicio": _hhmm(fr.HoraInicio),
               "cancha": canchas[f.CanchaId].Nombre if f.CanchaId in canchas else f.CanchaId,
               "estado": f.Estado, "creada_en": f.CreadaEn.isoformat(timespec="minutes") if f.CreadaEn else "",
               "antelacion_dias": round(antel, 2) if antel is not None else "",
               "fin_de_semana": 1 if f.Fecha.weekday() >= 4 else 0,
               "cliente": nombres.get(f.UsuarioId, ""),
               "segmento_ia": m["segmentos"]["por_usuario"].get(f.UsuarioId, "Nuevo")}


def dataset_resumen(db: Session, muestra: int = 25):
    m = _modelo(db)
    filas = list(_filas_dataset(db, m))
    por = {k: defaultdict(lambda: [0, 0]) for k in ("dia", "hora", "cancha", "mes")}
    for f in filas:
        canc = 1 if f["estado"] == "cancelada" else 0
        for k, v in (("dia", DIAS[f["dia_semana"]][:3]), ("hora", f["hora_inicio"]),
                     ("cancha", f["cancha"]), ("mes", f["fecha"][:7])):
            por[k][v][0] += 1 - canc
            por[k][v][1] += canc
    orden_dia = [d[:3] for d in DIAS]
    dist = lambda k, orden=None: [{"clave": c, "confirmadas": v[0], "canceladas": v[1]}  # noqa: E731
                                  for c, v in sorted(por[k].items(), key=lambda kv: orden.index(kv[0]) if orden else kv[0])]
    return {
        "filas": len(filas), "clientes": len({f["cliente"] for f in filas}),
        "desde": filas[-1]["fecha"] if filas else None, "hasta": filas[0]["fecha"] if filas else None,
        "confirmadas": sum(1 for f in filas if f["estado"] == "confirmada"),
        "canceladas": sum(1 for f in filas if f["estado"] == "cancelada"),
        "columnas": [{"nombre": n, "descripcion": d} for n, d in COLUMNAS_DATASET],
        "por_dia": dist("dia", orden_dia), "por_hora": dist("hora"), "por_cancha": dist("cancha"), "por_mes": dist("mes"),
        "muestra": filas[:muestra],
    }


def dataset_csv(db: Session):
    import csv
    import io
    m = _modelo(db)
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=[c for c, _ in COLUMNAS_DATASET])
    w.writeheader()
    for f in _filas_dataset(db, m):
        w.writerow(f)
    return buf.getvalue()


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
        "heatmap": heat, "pronostico": pronostico, "segmentos": m["segmentos"]["resumen"],
        "cancelacion": {"metricas": mc["metricas"], "coeficientes": mc["coeficientes"],
                        "en_riesgo": proximas[:8]},
        "insights": insights,
    }
