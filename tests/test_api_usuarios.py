"""Tests de los endpoints de usuarios: registro, inicio de sesión, cambio de contraseña y baja lógica (RF15/HU20)."""

import os
import sys
import unittest

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.main import app
from tests.conftest import CONTRASENA_PRUEBAS

NUEVO_RESIDENTE = {
    "usuario": "residente-ana",
    "nombre": "Ana Gómez",
    "email": "ana.gomez@cimas.example",
    "rol": "Residente de obra",
    "obra_id": "OBRA-NORTE-01",
    "contrasena": "contrasena-de-prueba",
}


class TestRegistro(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_registra_y_nunca_devuelve_la_contrasena(self):
        respuesta = self.client.post("/api/usuarios", json=NUEVO_RESIDENTE)

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["usuario"], "RESIDENTE-ANA")
        self.assertEqual(cuerpo["obra_id"], "OBRA-NORTE-01")
        self.assertNotIn("contrasena", cuerpo)
        self.assertNotIn(NUEVO_RESIDENTE["contrasena"], respuesta.text)

    def test_usuario_o_correo_repetido_responde_409(self):
        self.client.post("/api/usuarios", json=NUEVO_RESIDENTE)
        mismo_usuario = {**NUEVO_RESIDENTE, "email": "otra@cimas.example"}
        mismo_correo = {**NUEVO_RESIDENTE, "usuario": "RESIDENTE-ANA2"}

        self.assertEqual(self.client.post("/api/usuarios", json=mismo_usuario).status_code, 409)
        self.assertEqual(self.client.post("/api/usuarios", json=mismo_correo).status_code, 409)

    def test_residente_sin_obra_o_con_obra_inexistente_responde_422(self):
        sin_obra = {**NUEVO_RESIDENTE, "obra_id": None}
        obra_inexistente = {**NUEVO_RESIDENTE, "obra_id": "OBRA-NO-EXISTE"}

        self.assertEqual(self.client.post("/api/usuarios", json=sin_obra).status_code, 422)
        self.assertEqual(self.client.post("/api/usuarios", json=obra_inexistente).status_code, 422)

    def test_contrasena_corta_responde_422(self):
        corta = {**NUEVO_RESIDENTE, "contrasena": "1234"}
        self.assertEqual(self.client.post("/api/usuarios", json=corta).status_code, 422)


class TestSesion(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_inicia_sesion_sin_distinguir_mayusculas_en_el_usuario(self):
        respuesta = self.client.post("/api/sesion", json={"usuario": "admin-laura", "contrasena": CONTRASENA_PRUEBAS})

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.json()["rol"], "Administración")
        self.assertNotIn("contrasena", respuesta.json())

    def test_contrasena_incorrecta_y_usuario_inexistente_dan_el_mismo_401(self):
        incorrecta = self.client.post("/api/sesion", json={"usuario": "ADMIN-LAURA", "contrasena": "no-es-esta"})
        inexistente = self.client.post("/api/sesion", json={"usuario": "NADIE-AQUI", "contrasena": "no-es-esta"})

        self.assertEqual(incorrecta.status_code, 401)
        self.assertEqual(inexistente.status_code, 401)
        self.assertEqual(incorrecta.json(), inexistente.json())

    def test_la_cuenta_registrada_puede_iniciar_sesion(self):
        self.client.post("/api/usuarios", json=NUEVO_RESIDENTE)
        respuesta = self.client.post(
            "/api/sesion", json={"usuario": "RESIDENTE-ANA", "contrasena": NUEVO_RESIDENTE["contrasena"]}
        )
        self.assertEqual(respuesta.status_code, 200)


class TestAdministracionDeUsuarios(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_lista_filtrada_por_rol_sin_contrasenas(self):
        respuesta = self.client.get("/api/usuarios", params={"rol": "Residente de obra"})

        self.assertEqual(respuesta.status_code, 200)
        usuarios = respuesta.json()
        self.assertTrue(usuarios)
        self.assertTrue(all(u["rol"] == "Residente de obra" for u in usuarios))
        self.assertTrue(all("contrasena" not in u for u in usuarios))
        self.assertNotIn(CONTRASENA_PRUEBAS, respuesta.text)

    def test_obtiene_un_usuario_por_su_nombre(self):
        self.assertEqual(self.client.get("/api/usuarios/dir-carlos").json()["nombre"], "Carlos Ruiz")
        self.assertEqual(self.client.get("/api/usuarios/NADIE-AQUI").status_code, 404)

    def test_cambio_de_contrasena_exige_la_actual(self):
        usuario = self.client.get("/api/usuarios/CONT-SOFIA").json()
        ruta = f"/api/usuarios/{usuario['id']}/contrasena"

        mal = self.client.put(ruta, json={"actual": "no-es-esta", "nueva": "otra-contrasena"})
        corta = self.client.put(ruta, json={"actual": CONTRASENA_PRUEBAS, "nueva": "123"})
        bien = self.client.put(ruta, json={"actual": CONTRASENA_PRUEBAS, "nueva": "otra-contrasena"})

        self.assertEqual(mal.status_code, 422)
        self.assertEqual(corta.status_code, 422)
        self.assertEqual(bien.status_code, 200)
        nueva = self.client.post("/api/sesion", json={"usuario": "CONT-SOFIA", "contrasena": "otra-contrasena"})
        self.assertEqual(nueva.status_code, 200)

    def test_baja_logica_impide_iniciar_sesion_y_conserva_el_registro(self):
        usuario = self.client.get("/api/usuarios/RESIDENTE-LUIS").json()

        self.assertEqual(self.client.delete(f"/api/usuarios/{usuario['id']}").status_code, 204)
        self.assertEqual(self.client.get("/api/usuarios/RESIDENTE-LUIS").status_code, 404)
        sesion = self.client.post("/api/sesion", json={"usuario": "RESIDENTE-LUIS", "contrasena": CONTRASENA_PRUEBAS})
        self.assertEqual(sesion.status_code, 401)
        self.assertEqual(self.client.delete(f"/api/usuarios/{usuario['id']}").status_code, 404)
        # No se puede volver a registrar el mismo usuario: el registro sigue en la base
        repetido = {**NUEVO_RESIDENTE, "usuario": "RESIDENTE-LUIS"}
        self.assertEqual(self.client.post("/api/usuarios", json=repetido).status_code, 409)


class TestPantallas(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_todas_las_pantallas_cargan_la_sesion_antes_que_la_estructura(self):
        for pagina in (
            "index.html", "solicitud.html", "autorizacion.html", "saldos.html", "comprobante.html",
            "revision.html", "obras.html", "usuarios.html", "cuenta.html", "pruebas.html",
        ):
            with self.subTest(pagina=pagina):
                html = self.client.get(f"/app/{pagina}").text
                self.assertIn('<script src="sesion.js">', html)
                self.assertLess(html.index('src="sesion.js"'), html.index('src="shell.js"'))

    def test_la_pantalla_de_acceso_no_usa_la_estructura(self):
        html = self.client.get("/app/login.html").text
        self.assertIn('<script src="login.js">', html)
        self.assertNotIn("shell.js", html)


if __name__ == "__main__":
    unittest.main()
