"""Mide el tiempo de respuesta de las operaciones principales (RNF03: menos de 2 s).

Hace N llamadas a cada ruta y reporta la mediana (p50), el percentil 95 y el maximo.
Requiere el servidor corriendo. Uso (desde backend/): python scripts/medir_tiempos.py [--n 30]
"""
import argparse
import json
import statistics
import time
import urllib.request
from datetime import date, timedelta

def llamar(base, path, token=None, data=None):
    req = urllib.request.Request(base + path, data=json.dumps(data).encode() if data else None,
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    t0 = time.perf_counter()
    with urllib.request.urlopen(req) as r:
        cuerpo = r.read()
    return (time.perf_counter() - t0) * 1000, json.loads(cuerpo or b"{}") if r.headers.get_content_type() == "application/json" else None

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=30)
    ap.add_argument("--base", default="http://localhost:8000")
    a = ap.parse_args()
    _, r = llamar(a.base, "/auth/login", data={"email": "daniel@correo.com", "password": "cliente123"})
    cli = r["access_token"]
    _, r = llamar(a.base, "/auth/login", data={"email": "admin@goltime.com", "password": "admin123"})
    adm = r["access_token"]
    manana = date.today() + timedelta(days=1)
    rutas = [
        ("Consultar disponibilidad", f"/disponibilidad?cancha_id=1&fecha={manana}", None),
        ("Demanda estimada (IA)", f"/ia/demanda?cancha_id=1&fecha={manana}", None),
        ("Mis reservas", "/reservas", cli),
        ("Recomendaciones (IA)", "/ia/recomendaciones", cli),
        ("Perfil de juego (IA)", "/ia/mi-perfil", cli),
        ("Tablero de IA (admin)", "/admin/ia", adm),
        ("Clientes (admin)", "/admin/ia/clientes", adm),
        ("Dataset (admin)", "/admin/ia/dataset", adm),
    ]
    print(f"Tiempos de respuesta ({a.n} llamadas por ruta) - {date.today()}")
    print(f"{'Operacion':<28}{'p50 (ms)':>10}{'p95 (ms)':>10}{'max (ms)':>10}  RNF03")
    for nombre, path, tok in rutas:
        ts = sorted(llamar(a.base, path, tok)[0] for _ in range(a.n))
        p95 = ts[int(0.95 * (len(ts) - 1))]
        print(f"{nombre:<28}{statistics.median(ts):>10.1f}{p95:>10.1f}{ts[-1]:>10.1f}  {'cumple' if ts[-1] < 2000 else 'NO cumple'}")

if __name__ == "__main__":
    main()
