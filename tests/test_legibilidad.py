"""Pruebas de la revisión con OCR de las fotos de comprobantes (RNF05/HU21).

Se generan fotos sintéticas: un ticket nítido, el mismo ticket borroso, una imagen sin texto y un texto
sin ningún monto. Solo la primera debe guardarse; las demás se rechazan con un mensaje para repetirla.
"""

import os
import sys
import unittest
from io import BytesIO

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image, ImageDraw, ImageFilter, ImageFont

from src.services import legibilidad
from src.services.comprobante_service import comprobante_service
from tests.test_hu16_captura_rapida import RESIDENTE, BaseComprobanteTestCase

LINEAS_TICKET = [
    "LA ALACENA",
    "Fecha: 13/11/2026 15:20",
    "TRANSACCION APROBADA",
    "Cemento gris 50 kg",
    "Varilla corrugada 3/8",
    "Subtotal $108.62",
    "IVA 16% $17.38",
    "Total $126.00",
    "Gracias por su compra",
]
LINEAS_SIN_MONTO = [
    "LA ALACENA",
    "Gracias por su compra",
    "Vuelva pronto",
    "Esta es una nota sin cantidades",
    "Atencion a clientes",
    "Horario de lunes a sabado",
]


def foto_con_texto(lineas, desenfoque=0):
    imagen = Image.new("RGB", (1200, 1600), "white")
    dibujo = ImageDraw.Draw(imagen)
    fuente = ImageFont.load_default(size=56)
    for numero, linea in enumerate(lineas):
        dibujo.text((80, 100 + numero * 120), linea, fill="black", font=fuente)
    if desenfoque:
        imagen = imagen.filter(ImageFilter.GaussianBlur(desenfoque))
    return a_jpeg(imagen)


def foto_sin_texto():
    imagen = Image.new("RGB", (1200, 1600), "white")
    dibujo = ImageDraw.Draw(imagen)
    for x in range(0, 1200, 40):
        dibujo.line([(x, 0), (1200 - x, 1600)], fill=(30, 60, 160), width=6)
    return a_jpeg(imagen)


def a_jpeg(imagen):
    salida = BytesIO()
    imagen.save(salida, "JPEG", quality=92)
    return salida.getvalue()


class TestMotivoDeRechazo(unittest.TestCase):
    """Reglas de decisión sobre una lectura ya hecha (sin correr el OCR)."""

    TEXTOS = ["Ticket", "Cemento", "Varilla", "Subtotal", "Total $126.00"]

    def test_acepta_una_lectura_nitida_con_monto(self):
        self.assertIsNone(legibilidad.motivo_de_rechazo(self.TEXTOS, [0.99] * 5))

    def test_pocas_cajas_de_texto_es_foto_sin_texto(self):
        self.assertEqual(legibilidad.motivo_de_rechazo(self.TEXTOS[:2], [0.99] * 2), legibilidad.MENSAJE_SIN_TEXTO)
        self.assertEqual(legibilidad.motivo_de_rechazo([], []), legibilidad.MENSAJE_SIN_TEXTO)

    def test_confianza_baja_es_foto_borrosa(self):
        self.assertEqual(legibilidad.motivo_de_rechazo(self.TEXTOS, [0.6] * 5), legibilidad.MENSAJE_BORROSA)

    def test_sin_ningun_monto_no_parece_comprobante(self):
        textos = ["Teclado", "Alt Gr", "Ctrl", "Shift", "Enter"]

        self.assertEqual(legibilidad.motivo_de_rechazo(textos, [0.99] * 5), legibilidad.MENSAJE_SIN_MONTO)

    def test_reconoce_los_formatos_de_monto(self):
        for monto in ("$125", "$ 1,250.50", "125.00", "1.250,50"):
            with self.subTest(monto=monto):
                self.assertTrue(legibilidad.MONTO.search("Total " + monto))


class TestRevisarLegibilidad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.ticket = foto_con_texto(LINEAS_TICKET)
        cls.borrosa = foto_con_texto(LINEAS_TICKET, desenfoque=14)
        cls.sin_texto = foto_sin_texto()
        cls.sin_monto = foto_con_texto(LINEAS_SIN_MONTO)

    def test_ticket_nitido_se_acepta(self):
        legibilidad.revisar_legibilidad(self.ticket)

    def test_ticket_borroso_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            legibilidad.revisar_legibilidad(self.borrosa)

        self.assertIn(str(error.exception), (legibilidad.MENSAJE_SIN_TEXTO, legibilidad.MENSAJE_BORROSA))

    def test_imagen_sin_texto_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            legibilidad.revisar_legibilidad(self.sin_texto)

        self.assertEqual(str(error.exception), legibilidad.MENSAJE_SIN_TEXTO)

    def test_texto_sin_monto_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            legibilidad.revisar_legibilidad(self.sin_monto)

        self.assertEqual(str(error.exception), legibilidad.MENSAJE_SIN_MONTO)

    def test_archivo_que_no_es_imagen_se_rechaza(self):
        with self.assertRaises(ValueError) as error:
            legibilidad.revisar_legibilidad(b"esto no es una imagen")

        self.assertEqual(str(error.exception), legibilidad.MENSAJE_NO_ES_IMAGEN)


class TestCapturaConRevisionDeTexto(BaseComprobanteTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ticket = foto_con_texto(LINEAS_TICKET)
        cls.sin_texto = foto_sin_texto()

    def setUp(self):
        super().setUp()
        comprobante_service.validar_legibilidad = True

    def test_ticket_legible_se_guarda(self):
        respuesta = self.capturar(contenido=self.ticket)

        self.assertEqual(respuesta.status_code, 201)
        self.assertEqual(respuesta.json()["estado"], "Borrador")

    def test_foto_ilegible_se_rechaza_con_422_y_no_se_guarda_nada(self):
        respuesta = self.capturar(contenido=self.sin_texto)

        self.assertEqual(respuesta.status_code, 422)
        self.assertEqual(respuesta.json()["detail"], legibilidad.MENSAJE_SIN_TEXTO)
        listado = self.client.get("/api/comprobantes", params={"solicitante_id": RESIDENTE})
        self.assertEqual(listado.json(), [])
        self.assertEqual(os.listdir(self._tmp.name), [])

    def test_la_revision_se_puede_apagar_con_la_variable_de_entorno(self):
        comprobante_service.validar_legibilidad = False

        respuesta = self.capturar(contenido=self.sin_texto)

        self.assertEqual(respuesta.status_code, 201)


if __name__ == "__main__":
    unittest.main()
