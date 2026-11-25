"""Pruebas de la lectura del comprobante al escanear (RF11/HU11).

Al subir la foto, el servidor lee el ticket con OCR, guarda lo que reconoce en `lectura` y deja por
completar lo que no. La foto se puede volver a ver desde el comprobante.
"""

import os
import sys
import unittest
from unittest.mock import patch
from uuid import uuid4

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, inspect, text

from src import database
from src.services.comprobante_service import comprobante_service
from tests.test_hu16_captura_rapida import RESIDENTE, BaseComprobanteTestCase
from tests.test_legibilidad import LINEAS_TICKET, foto_con_texto

LINEAS_SIN_FECHA = [
    "FERRETERIA EL CLAVO",
    "Cemento gris 50 kg",
    "Varilla corrugada 3/8",
    "Pegamento epoxico",
    "Tornillos de acero",
    "Total $85.50",
]


class BaseLecturaTestCase(BaseComprobanteTestCase):
    @classmethod
    def setUpClass(cls):
        cls.ticket = foto_con_texto(LINEAS_TICKET)
        cls.ticket_sin_fecha = foto_con_texto(LINEAS_SIN_FECHA)

    def setUp(self):
        super().setUp()
        comprobante_service.validar_legibilidad = True


class TestLecturaAlCapturar(BaseLecturaTestCase):
    def test_precarga_proveedor_fecha_monto_y_tipo_del_ticket(self):
        respuesta = self.capturar(contenido=self.ticket)

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["lectura"]["proveedor"], "LA ALACENA")
        self.assertEqual(cuerpo["lectura"]["fecha_gasto"], "2026-11-13")
        self.assertEqual(cuerpo["lectura"]["monto_comprobado"], "126.00")
        self.assertEqual(cuerpo["lectura"]["tipo"], "ticket")
        self.assertEqual(cuerpo["lectura"]["faltantes"], [])

    def test_la_lectura_no_confirma_los_datos_el_comprobante_sigue_por_completar(self):
        cuerpo = self.capturar(contenido=self.ticket).json()

        self.assertIsNone(cuerpo["datos"])
        self.assertEqual(cuerpo["estado"], "Borrador")

    def test_lo_que_no_se_reconoce_queda_en_faltantes(self):
        cuerpo = self.capturar(contenido=self.ticket_sin_fecha).json()

        self.assertEqual(cuerpo["lectura"]["proveedor"], "FERRETERIA EL CLAVO")
        self.assertEqual(cuerpo["lectura"]["monto_comprobado"], "85.50")
        self.assertIsNone(cuerpo["lectura"]["fecha_gasto"])
        self.assertIn("fecha_gasto", cuerpo["lectura"]["faltantes"])

    def test_la_lectura_se_guarda_y_se_puede_consultar_despues(self):
        creado = self.capturar(contenido=self.ticket).json()

        consultado = self.client.get(f"/api/comprobantes/{creado['id']}").json()
        listado = self.client.get("/api/comprobantes", params={"solicitante_id": RESIDENTE}).json()

        self.assertEqual(consultado["lectura"], creado["lectura"])
        self.assertEqual(listado[0]["lectura"]["monto_comprobado"], "126.00")

    def test_con_la_revision_apagada_no_hay_lectura(self):
        comprobante_service.validar_legibilidad = False

        cuerpo = self.capturar(contenido=self.ticket).json()

        self.assertIsNone(cuerpo["lectura"])


class TestVerFotoDelComprobante(BaseLecturaTestCase):
    def test_devuelve_la_foto_que_se_subio(self):
        comprobante_id = self.capturar(contenido=self.ticket).json()["id"]

        respuesta = self.client.get(f"/api/comprobantes/{comprobante_id}/imagen")

        self.assertEqual(respuesta.status_code, 200)
        self.assertEqual(respuesta.headers["content-type"], "image/jpeg")
        self.assertEqual(respuesta.content, self.ticket)

    def test_un_comprobante_que_no_existe_responde_404(self):
        respuesta = self.client.get(f"/api/comprobantes/{uuid4()}/imagen")

        self.assertEqual(respuesta.status_code, 404)

    def test_un_borrador_descartado_ya_no_muestra_su_foto(self):
        comprobante_id = self.capturar(contenido=self.ticket).json()["id"]
        self.client.delete(f"/api/comprobantes/{comprobante_id}")

        respuesta = self.client.get(f"/api/comprobantes/{comprobante_id}/imagen")

        self.assertEqual(respuesta.status_code, 404)


class TestColumnasNuevas(unittest.TestCase):
    def test_agrega_la_columna_lectura_a_una_base_de_una_version_anterior(self):
        motor = create_engine("sqlite://")
        with motor.begin() as conexion:
            conexion.execute(text("CREATE TABLE comprobantes (id CHAR(32) PRIMARY KEY, estado VARCHAR(30))"))
            conexion.execute(text("INSERT INTO comprobantes (id, estado) VALUES ('abc', 'Borrador')"))

        with patch.object(database, "engine", motor):
            database.agregar_columnas_faltantes()

        columnas = {columna["name"] for columna in inspect(motor).get_columns("comprobantes")}
        with motor.connect() as conexion:
            filas = conexion.execute(text("SELECT id, estado, lectura FROM comprobantes")).fetchall()
        self.assertIn("lectura", columnas)
        self.assertEqual([tuple(fila) for fila in filas], [("abc", "Borrador", None)])


if __name__ == "__main__":
    unittest.main()
