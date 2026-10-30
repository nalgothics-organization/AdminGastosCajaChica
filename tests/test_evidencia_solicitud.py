"""Tests de la fotografía de evidencia de una solicitud de fondo (RF01/HU01)."""

import os
import sys

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from tests.test_hu16_captura_rapida import JPEG_VALIDO, BaseComprobanteTestCase


class TestEvidenciaSolicitud(BaseComprobanteTestCase):
    def subir(self, contenido=JPEG_VALIDO, content_type="image/jpeg"):
        return self.client.post(
            "/api/solicitudes/evidencia",
            files={"imagen": ("dano.jpg", contenido, content_type)},
        )

    def test_la_foto_se_guarda_y_se_puede_consultar(self):
        respuesta = self.subir()

        self.assertEqual(respuesta.status_code, 201)
        url = respuesta.json()["evidencia_url"]
        self.assertTrue(url.startswith("/api/evidencias/"))
        foto = self.client.get(url)
        self.assertEqual(foto.status_code, 200)
        self.assertEqual(foto.content, JPEG_VALIDO)

    def test_rechaza_archivos_que_no_son_imagen(self):
        respuesta = self.subir(contenido=b"%PDF-1.4" + b"\x00" * (25 * 1024), content_type="application/pdf")

        self.assertEqual(respuesta.status_code, 422)

    def test_rechaza_fotos_demasiado_pequenas(self):
        respuesta = self.subir(contenido=b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        self.assertEqual(respuesta.status_code, 422)

    def test_no_sirve_archivos_fuera_de_la_carpeta_de_evidencias(self):
        self.assertEqual(self.client.get("/api/evidencias/..%2Fsecreto.png").status_code, 404)
        self.assertEqual(self.client.get("/api/evidencias/inexistente.jpg").status_code, 404)

    def test_la_url_devuelta_sirve_como_evidencia_de_la_solicitud(self):
        url = self.subir().json()["evidencia_url"]

        respuesta = self.client.post("/api/solicitudes", json={
            "obra_id": "OBRA-NORTE-01",
            "solicitante_id": "RESIDENTE-PAU",
            "etapa_construccion": "acabados",
            "partida_categoria": "Materiales",
            "concepto": "Reposición de cristal dañado",
            "monto_solicitado": "1200.00",
            "costo_estimado": "1500.00",
            "urgencia": "alta",
            "evidencia_url": url,
        })

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["solicitud"]["evidencia_url"], url)
