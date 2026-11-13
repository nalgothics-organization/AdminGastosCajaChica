"""Tests de RNF01/HU16: captura del comprobante en máximo 3 toques.
La captura solo recibe la fotografía; ningún otro dato es obligatorio.
"""

import os
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.main import app
from src.models.solicitud import AprobacionCreate, SolicitudFondoCreate
from src.services.comprobante_service import comprobante_service
from src.services.solicitud_service import solicitud_service

RESIDENTE = "RESIDENTE-PAU"
JPEG_VALIDO = b"\xff\xd8\xff\xe0" + b"\x00" * (25 * 1024)


def crear_solicitud_aprobada(partida="Renta de Maquinaria", solicitante=RESIDENTE):
    respuesta = solicitud_service.crear_solicitud(
        SolicitudFondoCreate(
            obra_id="OBRA-NORTE-01",
            solicitante_id=solicitante,
            etapa_construccion="cimentación",
            partida_categoria=partida,
            concepto="Renta de retroexcavadora para sondeo",
            monto_solicitado=Decimal("3500.00"),
            costo_estimado=Decimal("4000.00"),
            urgencia="urgente",
            evidencia_url="https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
        )
    )
    return solicitud_service.aprobar_solicitud(
        respuesta.solicitud.id,
        AprobacionCreate(
            autorizador_id="ADMIN-LAURA",
            autorizador_nombre="Laura Méndez",
            rol_autorizador="Administración",
        ),
    )


class BaseComprobanteTestCase(unittest.TestCase):
    def setUp(self):
        # Reiniciar los almacenes en memoria y aislar las imágenes en una carpeta temporal
        self._tmp = tempfile.TemporaryDirectory()
        solicitud_service.__init__()
        comprobante_service.__init__(uploads_dir=self._tmp.name)
        self.client = TestClient(app)

    def tearDown(self):
        self._tmp.cleanup()

    def capturar(self, contenido=JPEG_VALIDO, content_type="image/jpeg", solicitante=RESIDENTE, solicitud_id=None):
        datos = {"solicitante_id": solicitante}
        if solicitud_id:
            datos["solicitud_id"] = str(solicitud_id)
        return self.client.post(
            "/api/comprobantes/captura",
            data=datos,
            files={"imagen": ("ticket.jpg", contenido, content_type)},
        )


class TestHU16CapturaRapida(BaseComprobanteTestCase):
    def test_criterio_1_pantalla_principal_tiene_boton_fotografiar(self):
        """Dado que abro la app, entonces encuentro el botón "Escanear comprobante"."""
        response = self.client.get("/app/")

        self.assertEqual(response.status_code, 200)
        self.assertIn("Escanear comprobante", response.text)
        self.assertIn('capture="environment"', response.text)

    def test_rnf05_boton_de_escaneo_fijo_y_revision_de_fotos_borrosas(self):
        """RNF05/HU21: botón fijo a la vista y aviso para repetir una foto borrosa u oscura."""
        response = self.client.get("/app/")

        self.assertIn("barra-escaneo", response.text)
        self.assertIn("revision-foto", response.text)

    def test_criterio_2_captura_solo_requiere_la_imagen(self):
        """El proceso no pide datos: solo la foto, sin tipo, monto ni solicitud."""
        crear_solicitud_aprobada()

        response = self.capturar()

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertEqual(body["estado"], "Borrador")
        self.assertIsNone(body["solicitud_id"])
        self.assertIsNone(body["datos"])
        self.assertTrue(Path(body["imagen_ruta"]).is_file())

    def test_la_foto_no_se_vincula_sola_aunque_haya_solicitudes_aprobadas(self):
        crear_solicitud_aprobada(partida="Renta de Maquinaria")
        crear_solicitud_aprobada(partida="Materiales")

        body = self.capturar().json()

        self.assertIsNone(body["solicitud_id"])
        self.assertIsNone(body["requiere_horas"])

    def test_la_foto_se_vincula_a_la_solicitud_que_el_residente_eligio(self):
        elegida = crear_solicitud_aprobada(partida="Renta de Maquinaria")
        crear_solicitud_aprobada(partida="Materiales")

        body = self.capturar(solicitud_id=elegida.id).json()

        self.assertEqual(body["solicitud_id"], str(elegida.id))
        self.assertEqual(body["obra_id"], "OBRA-NORTE-01")
        self.assertTrue(body["requiere_horas"])

    def test_no_se_captura_contra_la_solicitud_de_otro_residente(self):
        ajena = crear_solicitud_aprobada(solicitante="OTRO-RESIDENTE")

        response = self.capturar(solicitud_id=ajena.id)

        self.assertEqual(response.status_code, 422)
        self.assertEqual(comprobante_service.listar(), [])

    def test_sin_solicitud_aprobada_la_foto_se_guarda_igual(self):
        body = self.capturar().json()

        self.assertIsNone(body["solicitud_id"])
        self.assertIsNone(body["requiere_horas"])
        self.assertTrue(Path(body["imagen_ruta"]).is_file())

    def test_rechaza_archivo_que_no_es_imagen(self):
        response = self.capturar(contenido=b"%PDF-1.7" + b"\x00" * (25 * 1024), content_type="image/jpeg")

        self.assertEqual(response.status_code, 422)

    def test_rechaza_imagen_demasiado_pequena_para_ser_legible(self):
        response = self.capturar(contenido=b"\xff\xd8\xff\xe0" + b"\x00" * 100)

        self.assertEqual(response.status_code, 422)
        self.assertIn("legible", response.json()["detail"])

    def test_rechaza_imagen_que_excede_el_tamano_maximo(self):
        comprobante_service.tamano_maximo_bytes = 30 * 1024

        response = self.capturar(contenido=b"\xff\xd8\xff\xe0" + b"\x00" * (40 * 1024))

        self.assertEqual(response.status_code, 422)


if __name__ == "__main__":
    unittest.main()
