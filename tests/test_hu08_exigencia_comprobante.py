"""Pruebas de RF08/HU08: exigencia de comprobante válido y cierre al confirmar el escaneo.

Un gasto no se cierra sin su foto. Si la foto se lee completa y con confianza alta, la factura queda
comprobada y el ticket pasa a revisión de contabilidad sin más pasos; si falta algo, queda por completar.
"""

import os
import sys
import unittest
from unittest.mock import patch

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.comprobante_service import comprobante_service
from tests.test_hu07_comprobacion import DATOS_MAQUINARIA
from tests.test_hu16_captura_rapida import BaseComprobanteTestCase, crear_solicitud_aprobada

TICKET = ["LA ALACENA", "Fecha: 13/11/2026 15:20", "Cemento gris 50 kg", "Varilla corrugada", "Total $126.00"]
FACTURA = ["Materiales del Norte SA", "FACTURA A-1234", "Folio fiscal 8A3B", "Fecha: 13/11/2026", "Total $1,160.00"]
TICKET_SIN_FECHA = ["LA ALACENA", "Cemento gris 50 kg", "Varilla corrugada", "Pegamento", "Total $126.00"]


class BaseHU08TestCase(BaseComprobanteTestCase):
    def setUp(self):
        super().setUp()
        comprobante_service.validar_legibilidad = True
        comprobante_service.cierre_automatico = True

    def escanear(self, renglones, confianza=0.99, solicitud=None):
        """Sube una foto cuyo OCR devuelve `renglones`, vinculada a la solicitud indicada."""
        lectura = (renglones, [confianza] * len(renglones))
        datos = {"solicitud_id": str(solicitud.id)} if solicitud else {}
        with patch("src.services.comprobante_service.revisar_legibilidad", return_value=lectura):
            return self.client.post(
                "/api/comprobantes/captura",
                data={"solicitante_id": "RESIDENTE-PAU", **datos},
                files={"imagen": ("ticket.jpg", b"\xff\xd8\xff\xe0" + b"\x00" * (25 * 1024), "image/jpeg")},
            )


class TestExigenciaDeComprobante(BaseHU08TestCase):
    def test_criterio_1_no_se_cierra_un_gasto_sin_comprobante_adjunto(self):
        """Dado un gasto sin foto, cuando se intenta cerrar, entonces el sistema se lo impide."""
        comprobante_service.validar_legibilidad = False  # la foto es un archivo de prueba sin texto
        solicitud = crear_solicitud_aprobada(partida="Renta de Maquinaria")
        comprobante = self.capturar().json()
        datos = DATOS_MAQUINARIA | {"solicitud_id": str(solicitud.id)}
        self.client.put(f"/api/comprobantes/{comprobante['id']}/datos", json=datos)
        os.remove(comprobante["imagen_ruta"])

        respuesta = self.client.post(f"/api/comprobantes/{comprobante['id']}/cerrar")

        self.assertEqual(respuesta.status_code, 422)
        self.assertIn("comprobante adjunto", respuesta.json()["detail"])
        estado = self.client.get(f"/api/comprobantes/{comprobante['id']}").json()["estado"]
        self.assertEqual(estado, "Borrador")


class TestCierreAutomatico(BaseHU08TestCase):
    def test_criterio_3_la_factura_leida_completa_queda_comprobada_sin_mas_pasos(self):
        solicitud = crear_solicitud_aprobada(partida="Materiales")

        respuesta = self.escanear(FACTURA, solicitud=solicitud)

        self.assertEqual(respuesta.status_code, 201)
        cuerpo = respuesta.json()
        self.assertEqual(cuerpo["estado"], "Comprobado")
        self.assertTrue(cuerpo["cierre_automatico"])
        self.assertEqual(cuerpo["datos"]["tipo"], "factura")
        self.assertEqual(cuerpo["datos"]["monto_comprobado"], "1160.00")
        self.assertEqual(cuerpo["datos"]["concepto"], solicitud.concepto)

    def test_criterio_2_el_ticket_leido_completo_pasa_solo_a_revision_de_contabilidad(self):
        solicitud = crear_solicitud_aprobada(partida="Materiales")

        cuerpo = self.escanear(TICKET, solicitud=solicitud).json()

        self.assertEqual(cuerpo["estado"], "Revisión contabilidad")
        self.assertTrue(cuerpo["cierre_automatico"])
        self.assertEqual(cuerpo["datos"]["tipo"], "ticket")

    def test_el_cierre_automatico_se_guarda_y_ya_no_se_puede_editar(self):
        solicitud = crear_solicitud_aprobada(partida="Materiales")
        comprobante_id = self.escanear(TICKET, solicitud=solicitud).json()["id"]

        consultado = self.client.get(f"/api/comprobantes/{comprobante_id}").json()
        edicion = self.client.put(
            f"/api/comprobantes/{comprobante_id}/datos", json=DATOS_MAQUINARIA | {"solicitud_id": str(solicitud.id)}
        )

        self.assertTrue(consultado["cierre_automatico"])
        self.assertEqual(edicion.status_code, 409)

    def test_si_falta_un_dato_queda_por_completar(self):
        solicitud = crear_solicitud_aprobada(partida="Materiales")

        cuerpo = self.escanear(TICKET_SIN_FECHA, solicitud=solicitud).json()

        self.assertEqual(cuerpo["estado"], "Borrador")
        self.assertIsNone(cuerpo["datos"])
        self.assertIsNone(cuerpo["cierre_automatico"])
        self.assertEqual(cuerpo["lectura"]["faltantes"], ["fecha_gasto"])

    def test_con_confianza_baja_no_se_cierra_solo(self):
        solicitud = crear_solicitud_aprobada(partida="Materiales")

        cuerpo = self.escanear(TICKET, confianza=0.88, solicitud=solicitud).json()

        self.assertEqual(cuerpo["estado"], "Borrador")
        self.assertIsNone(cuerpo["datos"])

    def test_si_la_partida_pide_horas_queda_por_completar(self):
        solicitud = crear_solicitud_aprobada(partida="Renta de Maquinaria")

        cuerpo = self.escanear(TICKET, solicitud=solicitud).json()

        self.assertEqual(cuerpo["estado"], "Borrador")
        self.assertTrue(cuerpo["requiere_horas"])

    def test_sin_solicitud_queda_por_completar(self):
        crear_solicitud_aprobada(partida="Materiales")

        cuerpo = self.escanear(TICKET).json()

        self.assertEqual(cuerpo["estado"], "Borrador")
        self.assertIsNone(cuerpo["solicitud_id"])

    def test_se_puede_desactivar_con_la_variable_de_entorno(self):
        comprobante_service.cierre_automatico = False
        solicitud = crear_solicitud_aprobada(partida="Materiales")

        cuerpo = self.escanear(TICKET, solicitud=solicitud).json()

        self.assertEqual(cuerpo["estado"], "Borrador")
        self.assertEqual(cuerpo["lectura"]["monto_comprobado"], "126.00")


if __name__ == "__main__":
    unittest.main()
