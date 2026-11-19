"""Pruebas del dataset ficticio, del modulo de IA y de su API.

Se ejecutan contra una base SQLite TEMPORAL (no tocan PostgreSQL):

    cd backend
    python -m unittest tests.test_ia -v

Que se comprueba:
  * El dataset se genera completo y respeta la regla de oro: nunca dos reservas
    confirmadas en la misma cancha, fecha y franja.
  * La IA reconoce el patron de cada perfil demo (tipo de jugador, dia y hora habitual)
    y le recomienda su franja de siempre.
  * Los modelos aprenden lo que el generador escondio en los datos (hora pico,
    efecto de la antelacion y del historial en la cancelacion).
  * La API responde, protege las rutas de administrador y mantiene el control de doble
    reserva, incluso con 8 peticiones simultaneas sobre la misma franja.
"""
import json
import os
import socket
import sys
import tempfile
import threading
import time
import unittest
import urllib.error
import urllib.request
from collections import Counter
from datetime import date, timedelta
from pathlib import Path

_TMP = tempfile.mkdtemp(prefix="goltime_test_")
os.environ["DATABASE_URL"] = f"sqlite:///{_TMP}/test.db"
os.environ["SQL_ECHO"] = "false"
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

import scripts.generar_dataset as gen  # noqa: E402
gen.CSV_SALIDA = Path(_TMP) / "dataset.csv"  # no sobrescribir el CSV del repositorio

from app.db import models  # noqa: E402
from app.db.session import SessionLocal  # noqa: E402
from app.services import ia_service as ia  # noqa: E402

ESPERADO = {
    "daniel@correo.com": ("Fieles", "Martes", "20:00", "Cancha 1"),
    "laura@demo.goltime.co": ("Fin de semana", "Sábado", "19:00", "Cancha 2"),
    "andres@demo.goltime.co": ("En riesgo", None, None, None),
    "julian@demo.goltime.co": ("Fieles", "Lunes", "18:00", "Cancha 3"),
    "camila@demo.goltime.co": ("Ocasionales", None, None, None),
}


def setUpModule():
    gen.generar(verbose=False)


class TestDataset(unittest.TestCase):
    def setUp(self):
        self.db = SessionLocal()

    def tearDown(self):
        self.db.close()

    def test_volumen(self):
        n = self.db.query(models.Reserva).count()
        clientes = self.db.query(models.Usuario).filter(models.Usuario.Rol == "cliente").count()
        self.assertGreater(n, 1200, "el dataset debe tener mas de 1200 reservas")
        self.assertGreaterEqual(clientes, 120)

    def test_sin_doble_reserva(self):
        confirmadas = Counter((r.CanchaId, r.FranjaId, r.Fecha) for r in
                              self.db.query(models.Reserva).filter(models.Reserva.Estado == "confirmada"))
        repetidas = [k for k, v in confirmadas.items() if v > 1]
        self.assertEqual(repetidas, [], "no puede haber dos confirmadas en el mismo cupo")

    def test_perfiles_demo_tienen_historia(self):
        for email in ESPERADO:
            u = self.db.query(models.Usuario).filter(models.Usuario.Email == email).one()
            n = self.db.query(models.Reserva).filter(models.Reserva.UsuarioId == u.UsuarioId).count()
            self.assertGreaterEqual(n, 6, email)

    def test_csv(self):
        lineas = gen.CSV_SALIDA.read_text(encoding="utf-8").splitlines()
        self.assertTrue(lineas[0].startswith("fecha,dia_semana,hora_inicio"))
        self.assertGreater(len(lineas), 1200)


class TestPatrones(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.ids = {u.Email: u.UsuarioId for u in cls.db.query(models.Usuario)}

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_tipo_de_jugador(self):
        for email, (segmento, *_rest) in ESPERADO.items():
            p = ia.mi_perfil(self.db, self.ids[email])
            self.assertEqual(p["segmento"]["nombre"], segmento, f"{email}: {p['patron']}")

    def test_combinacion_favorita(self):
        for email, (_, dia, hora, cancha) in ESPERADO.items():
            if not dia:
                continue
            p = ia.mi_perfil(self.db, self.ids[email])
            top = p["favoritos"]["combos"][0]
            self.assertEqual((top["dia"], top["hora"]), (dia, hora), email)
            self.assertEqual(p["favoritos"]["cancha"], cancha, email)

    def test_recomienda_su_clasico(self):
        """Cada perfil con rutina recibe entre sus sugerencias una franja de su rutina."""
        rutinas = {e: {(d, h) for d, h, _, _ in next(p for p in gen.PERFILES_DEMO if p["email"] == e)["habitos"]}
                   for e in ESPERADO if ESPERADO[e][1]}
        for email, rutina in rutinas.items():
            items = ia.recomendaciones(self.db, self.ids[email])["items"]
            self.assertTrue(items, email)
            sugeridas = {(date.fromisoformat(i["fecha"]).weekday(), int(i["hora_inicio"][:2])) for i in items}
            self.assertTrue(sugeridas & rutina, f"{email}: {items}")
            self.assertIn("clásico", " ".join(i["motivo"] for i in items), email)

    def test_ocasional_sin_clasico(self):
        p = ia.mi_perfil(self.db, self.ids["camila@demo.goltime.co"])
        self.assertIn("No tienes un día fijo", p["patron"])

    def test_recomendaciones_son_libres_y_futuras(self):
        items = ia.recomendaciones(self.db, self.ids["daniel@correo.com"])["items"]
        for i in items:
            ocupada = self.db.query(models.Reserva).filter(
                models.Reserva.CanchaId == i["cancha_id"], models.Reserva.FranjaId == i["franja_id"],
                models.Reserva.Fecha == date.fromisoformat(i["fecha"]),
                models.Reserva.Estado == "confirmada").count()
            self.assertEqual(ocupada, 0)
            self.assertGreaterEqual(date.fromisoformat(i["fecha"]), date.today())


class TestModelos(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.db = SessionLocal()
        cls.r = ia.resumen_admin(cls.db)

    @classmethod
    def tearDownClass(cls):
        cls.db.close()

    def test_hora_pico_aprendida(self):
        celdas = {(h["dia"], c["hora"]): c["prediccion"] for h in self.r["heatmap"] for c in h["celdas"]}
        self.assertGreater(celdas[("Viernes", "19:00")], celdas[("Lunes", "18:00")] + 0.25)

    def test_modelo_cancelacion(self):
        m = self.r["cancelacion"]["metricas"]
        self.assertGreater(m["auc"], 0.62, m)
        self.assertGreater(m["lift"], 1.5, m)
        pesos = {c["variable"]: c["peso"] for c in self.r["cancelacion"]["coeficientes"]}
        self.assertGreater(pesos["Antelación (días)"], 0)
        self.assertGreater(pesos["Historial de cancelación del cliente"], 0)

    def test_cuatro_segmentos(self):
        self.assertEqual(sorted(g["nombre"] for g in self.r["segmentos"]),
                         ["En riesgo", "Fieles", "Fin de semana", "Ocasionales"])


def _puerto_libre():
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


class TestZApi(unittest.TestCase):
    """Se ejecuta de ultima (orden alfabetico) porque crea y cancela una reserva."""
    @classmethod
    def setUpClass(cls):
        import uvicorn
        from app.main import app
        cls.base = f"http://127.0.0.1:{_puerto_libre()}"
        port = int(cls.base.rsplit(":", 1)[1])
        cls.server = uvicorn.Server(uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error"))
        threading.Thread(target=cls.server.run, daemon=True).start()
        for _ in range(100):
            if cls.server.started:
                break
            time.sleep(0.05)
        cls.cliente = cls.login("daniel@correo.com", "cliente123")
        cls.admin = cls.login("admin@goltime.com", "admin123")

    @classmethod
    def tearDownClass(cls):
        cls.server.should_exit = True

    @classmethod
    def req(cls, path, token=None, body=None, method=None):
        h = {"Content-Type": "application/json"}
        if token:
            h["Authorization"] = "Bearer " + token
        data = json.dumps(body).encode() if body is not None else None
        r = urllib.request.Request(cls.base + path, data=data, headers=h, method=method or ("POST" if data else "GET"))
        try:
            with urllib.request.urlopen(r) as res:
                raw = res.read().decode()
                return res.status, (json.loads(raw) if res.headers.get_content_type() == "application/json" else raw)
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read().decode() or "{}")

    @classmethod
    def login(cls, email, clave):
        st, r = cls.req("/auth/login", body={"email": email, "password": clave})
        assert st == 200, r
        return r["access_token"]

    def test_perfiles_demo_pueden_entrar(self):
        for email in ESPERADO:
            if email != "daniel@correo.com":
                self.assertTrue(self.login(email, gen.CLAVE_DEMO))

    def test_endpoints_cliente(self):
        st, p = self.req("/ia/mi-perfil", self.cliente)
        self.assertEqual(st, 200)
        self.assertEqual(p["segmento"]["nombre"], "Fieles")
        st, _ = self.req("/ia/recomendaciones", self.cliente)
        self.assertEqual(st, 200)
        st, dem = self.req(f"/ia/demanda?cancha_id=1&fecha={date.today() + timedelta(days=2)}")
        self.assertEqual(st, 200)
        self.assertTrue(all(0 < d["probabilidad"] < 1 for d in dem))

    def test_rutas_admin_protegidas(self):
        for ruta in ("/admin/ia", "/admin/ia/clientes", "/admin/ia/dataset"):
            self.assertEqual(self.req(ruta, self.cliente)[0], 403, ruta)
            self.assertEqual(self.req(ruta)[0], 401, ruta)

    def test_endpoints_admin(self):
        for ruta in ("/admin/ia", "/admin/ia/clientes", "/admin/ia/dataset"):
            self.assertEqual(self.req(ruta, self.admin)[0], 200, ruta)
        st, csv = self.req("/admin/ia/dataset.csv", self.admin)
        self.assertEqual(st, 200)
        self.assertTrue(csv.startswith("reserva_id,fecha"))
        st, cs = self.req("/admin/ia/clientes", self.admin)
        demo = [c for c in cs if c["demo"]]
        self.assertEqual(len(demo), 5)
        st, p = self.req(f"/admin/ia/clientes/{demo[0]['usuario_id']}", self.admin)
        self.assertEqual(st, 200)
        self.assertIn("patron", p)

    def test_concurrencia_misma_franja(self):
        """8 peticiones simultaneas sobre la misma franja: exactamente una se confirma."""
        st, rec = self.req("/ia/recomendaciones", self.admin)
        r = rec["items"][-1]
        tokens = [self.cliente, self.login("laura@demo.goltime.co", gen.CLAVE_DEMO),
                  self.login("julian@demo.goltime.co", gen.CLAVE_DEMO)]
        body = {"cancha_id": r["cancha_id"], "franja_id": r["franja_id"], "fecha": r["fecha"],
                "nombre_contacto": "Prueba", "celular": "3000000000", "correo_contacto": "prueba@correo.com"}
        barrera, codigos = threading.Barrier(8), []

        def intentar(i):
            barrera.wait()
            codigos.append(self.req("/reservas", tokens[i % 3], body))
        hilos = [threading.Thread(target=intentar, args=(i,)) for i in range(8)]
        for h in hilos:
            h.start()
        for h in hilos:
            h.join()
        estados = sorted(c for c, _ in codigos)
        self.assertEqual(estados, [201] + [409] * 7, estados)
        db = SessionLocal()
        n = db.query(models.Reserva).filter(
            models.Reserva.CanchaId == r["cancha_id"], models.Reserva.FranjaId == r["franja_id"],
            models.Reserva.Fecha == date.fromisoformat(r["fecha"]), models.Reserva.Estado == "confirmada").count()
        db.close()
        self.assertEqual(n, 1)

    def test_reservar_recomendada_y_doble_reserva(self):
        st, rec = self.req("/ia/recomendaciones", self.cliente)
        r = rec["items"][0]
        body = {"cancha_id": r["cancha_id"], "franja_id": r["franja_id"], "fecha": r["fecha"],
                "nombre_contacto": "Daniel Viafara", "celular": "3001234567", "correo_contacto": "daniel@correo.com"}
        st, nueva = self.req("/reservas", self.cliente, body)
        self.assertEqual(st, 201)
        otro = self.login("laura@demo.goltime.co", gen.CLAVE_DEMO)
        self.assertEqual(self.req("/reservas", otro, body)[0], 409, "la doble reserva debe rechazarse")
        # el modelo se reentrena: la franja ya no se recomienda
        st, rec2 = self.req("/ia/recomendaciones", self.cliente)
        claves = {(i["cancha_id"], i["franja_id"], i["fecha"]) for i in rec2["items"]}
        self.assertNotIn((r["cancha_id"], r["franja_id"], r["fecha"]), claves)
        # cancelar libera el cupo
        st, c = self.req(f"/reservas/{nueva['reserva_id']}/cancelar", self.cliente, method="POST")
        self.assertEqual((st, c["estado"]), (200, "cancelada"))


if __name__ == "__main__":
    unittest.main(verbosity=2)
