"""Pruebas de validación de entrada: evidencia_url de la solicitud de fondo (RF01/HU01).

La API solo acepta una foto subida a /api/evidencias/ o un enlace http(s). Cualquier otro texto
(un esquema javascript:, una ruta de archivo o HTML) se rechaza antes de guardarse en la base.
Fuente: OWASP Input Validation Cheat Sheet (validación por lista de permitidos).
"""

import os
import sys
import unittest

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_api_solicitudes import BaseApiTestCase

FOTO_SUBIDA = "/api/evidencias/0b8f6c2e-1d4a-4f6b-9c3e-5a7d2e9f1b04.jpg"
MENSAJE = "La evidencia debe ser una foto subida o un enlace que empiece con http:// o https://."


class TestValidacionEvidencia(BaseApiTestCase):
    def test_acepta_la_foto_subida_a_la_api(self):
        respuesta = self.crear_solicitud(evidencia_url=FOTO_SUBIDA)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["solicitud"]["evidencia_url"], FOTO_SUBIDA)

    def test_acepta_un_enlace_https(self):
        respuesta = self.crear_solicitud(evidencia_url="https://storage.empresa.com/evidencias/fuga.jpg")

        self.assertEqual(respuesta.status_code, 201)

    def test_rechaza_un_enlace_javascript(self):
        respuesta = self.crear_solicitud(evidencia_url="javascript:alert(document.cookie)")

        self.assertEqual(respuesta.status_code, 422)
        self.assertIn(MENSAJE, respuesta.text)

    def test_rechaza_una_ruta_que_sale_de_la_carpeta_de_evidencias(self):
        respuesta = self.crear_solicitud(evidencia_url="/api/evidencias/../../.env")

        self.assertEqual(respuesta.status_code, 422)
        self.assertIn(MENSAJE, respuesta.text)

    def test_rechaza_html_incrustado_en_el_enlace(self):
        respuesta = self.crear_solicitud(evidencia_url='https://x.com/"><script>alert(1)</script>')

        self.assertEqual(respuesta.status_code, 422)

    def test_la_solicitud_rechazada_no_se_guarda(self):
        self.crear_solicitud(evidencia_url="javascript:alert(1)")

        self.assertEqual(self.client.get("/api/solicitudes").json(), [])


if __name__ == "__main__":
    unittest.main()
