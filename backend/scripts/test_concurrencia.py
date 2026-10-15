"""Dispara dos reservas sobre la misma franja a la vez.
Evidencia que el sistema confirma una sola (201) y rechaza la otra (409).
Requiere el servidor corriendo en http://localhost:8000.
Uso: python scripts/test_concurrencia.py
"""
import threading
import urllib.request
import json

BASE = "http://localhost:8000"


def _post(path, data, token=None):
    req = urllib.request.Request(BASE + path, data=json.dumps(data).encode(),
                                 headers={"Content-Type": "application/json"})
    if token:
        req.add_header("Authorization", "Bearer " + token)
    try:
        with urllib.request.urlopen(req) as r:
            return r.status, json.loads(r.read())
    except urllib.error.HTTPError as e:
        return e.code, json.loads(e.read())


def login():
    _, t = _post("/auth/login", {"email": "daniel@correo.com", "password": "cliente123"})
    return t["access_token"]


def main():
    token = login()
    payload = {"cancha_id": 1, "franja_id": 2, "fecha": "2026-11-01"}
    resultados = []

    def intentar():
        resultados.append(_post("/reservas", payload, token)[0])

    hilos = [threading.Thread(target=intentar) for _ in range(2)]
    for h in hilos:
        h.start()
    for h in hilos:
        h.join()

    print("Codigos obtenidos:", sorted(resultados))
    exitos = resultados.count(201)
    print("Confirmadas:", exitos, "| Rechazadas (409):", resultados.count(409))
    print("RESULTADO:", "OK (no hubo doble reserva)" if exitos == 1 else "REVISAR")


if __name__ == "__main__":
    main()
