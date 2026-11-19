"""Prueba de concurrencia: varios usuarios intentan reservar la MISMA franja al mismo tiempo.

Evidencia que el sistema confirma una sola reserva (201) y rechaza todas las demas (409),
gracias a la transaccion y al indice unico filtrado de la tabla Reserva.

  1. Busca una franja libre en los proximos dias.
  2. Inicia sesion con 5 usuarios distintos.
  3. Lanza N peticiones simultaneas (por defecto 10) sobre esa franja; una barrera hace
     que todos los hilos disparen en el mismo instante.
  4. Comprueba en la API que la franja quedo ocupada una sola vez.
  5. Cancela la reserva ganadora para dejar los datos como estaban (usar --conservar para no hacerlo).

Requiere el servidor corriendo (por defecto en http://localhost:8000).
Uso (desde backend/):  python scripts/test_concurrencia.py [--n 10] [--base URL]
"""
import argparse
import json
import threading
import time
import urllib.error
import urllib.request
from datetime import date, datetime, timedelta

USUARIOS = [("daniel@correo.com", "cliente123"), ("laura@demo.goltime.co", "demo1234"),
            ("andres@demo.goltime.co", "demo1234"), ("camila@demo.goltime.co", "demo1234"),
            ("julian@demo.goltime.co", "demo1234")]


def llamar(base, path, data=None, token=None, method=None):
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data is not None else None,
                                 headers={"Content-Type": "application/json"},
                                 method=method or ("POST" if data is not None else "GET"))
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read() or b"{}")
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read() or b"{}")


def franja_libre(base):
    ahora = datetime.now()
    _, canchas = llamar(base, "/canchas")
    for off in range(1, 15):
        d = date.today() + timedelta(days=off)
        for c in canchas:
            _, fs = llamar(base, f"/disponibilidad?cancha_id={c['cancha_id']}&fecha={d}")
            for f in fs:
                if f["estado"] == "libre" and datetime.combine(d, datetime.strptime(f["hora_inicio"], "%H:%M").time()) > ahora:
                    return c, f, d
    raise SystemExit("No se encontro ninguna franja libre en los proximos 14 dias.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10, help="peticiones simultaneas")
    ap.add_argument("--base", default="http://localhost:8000")
    ap.add_argument("--conservar", action="store_true", help="no cancelar la reserva ganadora")
    a = ap.parse_args()

    cancha, franja, dia = franja_libre(a.base)
    tokens = []
    for email, clave in USUARIOS:
        st, r = llamar(a.base, "/auth/login", {"email": email, "password": clave})
        if st == 200:
            tokens.append((email, r["access_token"]))
    print("=" * 66)
    print("PRUEBA DE CONCURRENCIA - GolTime")
    print("=" * 66)
    print(f"Franja objetivo : {cancha['nombre']} · {dia} · {franja['hora_inicio']}-{franja['hora_fin']}")
    print(f"Usuarios        : {len(tokens)} · peticiones simultaneas: {a.n}")

    barrera = threading.Barrier(a.n)
    resultados = []
    candado = threading.Lock()

    def intentar(i):
        email, tok = tokens[i % len(tokens)]
        cuerpo = {"cancha_id": cancha["cancha_id"], "franja_id": franja["franja_id"], "fecha": str(dia),
                  "nombre_contacto": "Prueba Concurrencia", "celular": "3000000000", "correo_contacto": email}
        barrera.wait()  # todos disparan en el mismo instante
        t0 = time.perf_counter()
        st, r = llamar(a.base, "/reservas", cuerpo, tok)
        with candado:
            resultados.append((i + 1, email, st, r, (time.perf_counter() - t0) * 1000))

    hilos = [threading.Thread(target=intentar, args=(i,)) for i in range(a.n)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    print("-" * 66)
    for i, email, st, r, ms in sorted(resultados):
        txt = "CONFIRMADA" if st == 201 else ("RECHAZADA: franja ya reservada" if st == 409 else f"ERROR {r}")
        print(f"  #{i:>2} {email:<26} HTTP {st}  {txt:<32} {ms:6.0f} ms")
    ok = [r for r in resultados if r[2] == 201]
    rech = [r for r in resultados if r[2] == 409]
    _, fs = llamar(a.base, f"/disponibilidad?cancha_id={cancha['cancha_id']}&fecha={dia}")
    estado = next(f["estado"] for f in fs if f["franja_id"] == franja["franja_id"])
    print("-" * 66)
    print(f"Confirmadas (201): {len(ok)}   Rechazadas (409): {len(rech)}   Otros: {a.n - len(ok) - len(rech)}")
    print(f"Estado final de la franja en la base de datos: {estado}")
    exito = len(ok) == 1 and len(rech) == a.n - 1 and estado == "ocupada"
    print("RESULTADO:", "OK - no hubo doble reserva" if exito else "FALLO - revisar")
    if ok and not a.conservar:
        _, email, _, r, _ = ok[0]
        tok = dict(tokens)[email]
        st, _ = llamar(a.base, f"/reservas/{r['reserva_id']}/cancelar", {}, tok)
        print(f"Limpieza: reserva {r['reserva_id']} cancelada (HTTP {st}); la franja vuelve a estar libre.")
    print("=" * 66)
    raise SystemExit(0 if exito else 1)


if __name__ == "__main__":
    main()
