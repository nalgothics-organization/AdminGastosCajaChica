"""Pruebas de la extracción de datos del comprobante a partir del texto leído (RF11/HU11).

Se prueban las reglas sobre renglones ya leídos (sin correr el OCR): lo que se reconoce se precarga y
lo que no se reconoce queda en None para que el residente lo complete.
"""

import os
import sys
import unittest
from datetime import date, timedelta
from decimal import Decimal

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.comprobante import TipoComprobante
from src.services import extraccion

# Renglones tal como los lee el OCR en un ticket real de terminal bancaria
TICKET_REAL = [
    "LA ALACENA", "Fecha: Nov. 13, 2026 3:20 PM", "TRANSACCIÓN APROBADA", "Autorización: 006556",
    "Scotiabank i-Credito", "Mastercard", "****4788", "AID", "A0000000041010", "Afiliación", "9501369",
    "No. de recibo", "POqfGThH", "Autorizado sin firma", "Total", "$125.00",
    "Resumen de compra. informativo", "Para aclaraciones solicita", "tu e-voucher", "clip.mx",
]


class TestExtraerDatos(unittest.TestCase):
    def test_lee_proveedor_fecha_monto_y_tipo_de_un_ticket_real(self):
        lectura = extraccion.extraer_datos(TICKET_REAL, [0.99] * len(TICKET_REAL))

        self.assertEqual(lectura.proveedor, "LA ALACENA")
        self.assertEqual(lectura.fecha_gasto, date(2026, 11, 13))
        self.assertEqual(lectura.monto_comprobado, Decimal("125.00"))
        self.assertEqual(lectura.tipo, TipoComprobante.TICKET)
        self.assertEqual(lectura.faltantes, [])
        self.assertEqual(lectura.confianza, 0.99)

    def test_lo_que_no_se_reconoce_queda_por_completar(self):
        renglones = ["Ferretería El Clavo", "Cemento gris", "Tornillos", "Pegamento", "Total 85.50"]

        lectura = extraccion.extraer_datos(renglones, [0.9] * 5)

        self.assertEqual(lectura.proveedor, "Ferretería El Clavo")
        self.assertEqual(lectura.monto_comprobado, Decimal("85.50"))
        self.assertIsNone(lectura.fecha_gasto)
        self.assertEqual(lectura.faltantes, ["fecha_gasto"])

    def test_sin_texto_no_se_inventa_nada(self):
        lectura = extraccion.extraer_datos([], [])

        self.assertEqual(lectura.faltantes, ["tipo", "monto_comprobado", "fecha_gasto", "proveedor"])
        self.assertIsNone(lectura.confianza)
        self.assertEqual(lectura.renglones, [])

    def test_factura_se_distingue_del_ticket(self):
        renglones = ["Materiales del Norte SA", "FACTURA A-1234", "Folio fiscal 8A3B", "Total $1,160.00"]

        lectura = extraccion.extraer_datos(renglones, [0.95] * 4)

        self.assertEqual(lectura.tipo, TipoComprobante.FACTURA)
        self.assertEqual(lectura.monto_comprobado, Decimal("1160.00"))


class TestExtraerMonto(unittest.TestCase):
    def test_toma_el_total_y_no_el_subtotal_ni_el_iva(self):
        renglones = ["Subtotal $100.00", "IVA 16% $16.00", "Total $116.00"]

        self.assertEqual(extraccion.extraer_monto(renglones), Decimal("116.00"))

    def test_el_total_puede_estar_en_el_renglon_siguiente(self):
        self.assertEqual(extraccion.extraer_monto(["Total", "$125.00"]), Decimal("125.00"))

    def test_sin_renglon_de_total_toma_el_monto_mayor(self):
        self.assertEqual(extraccion.extraer_monto(["Cemento 60.00", "Varilla 240.50"]), Decimal("240.50"))

    def test_no_confunde_numeros_de_tarjeta_o_folio_con_montos(self):
        self.assertIsNone(extraccion.extraer_monto(["****4788", "9501369", "A0000000041010"]))

    def test_formatos_de_monto(self):
        casos = {"$125.00": "125.00", "$1,250.50": "1250.50", "1.250,50": "1250.50", "125,00": "125.00", "$85": "85.00"}
        for texto, esperado in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(extraccion.extraer_monto(["Total " + texto]), Decimal(esperado))


class TestExtraerFecha(unittest.TestCase):
    def test_formatos_de_fecha(self):
        casos = {
            "13/11/2026": date(2026, 11, 13),
            "13-11-26": date(2026, 11, 13),
            "2026-11-13": date(2026, 11, 13),
            "Nov. 13, 2026": date(2026, 11, 13),
            "13 de noviembre de 2026": date(2026, 11, 13),
            "Fecha: 05/Nov/2026 14:30": date(2026, 11, 5),
        }
        for texto, esperada in casos.items():
            with self.subTest(texto=texto):
                self.assertEqual(extraccion.extraer_fecha([texto]), esperada)

    def test_una_fecha_futura_o_imposible_no_se_acepta(self):
        manana = date.today() + timedelta(days=1)

        self.assertIsNone(extraccion.extraer_fecha([manana.strftime("%d/%m/%Y")]))
        self.assertIsNone(extraccion.extraer_fecha(["31/02/2026"]))

    def test_si_el_segundo_numero_no_es_mes_se_lee_mes_dia_anio(self):
        self.assertEqual(extraccion.extraer_fecha(["11/13/2026"]), date(2026, 11, 13))


class TestExtraerProveedor(unittest.TestCase):
    def test_salta_los_renglones_que_no_son_el_nombre_del_comercio(self):
        renglones = ["TICKET DE VENTA", "Fecha 13/11/2026", "Abarrotes Doña Mary", "Total $50.00"]

        self.assertEqual(extraccion.extraer_proveedor(renglones), "Abarrotes Doña Mary")

    def test_sin_un_nombre_claro_queda_por_completar(self):
        self.assertIsNone(extraccion.extraer_proveedor(["12345", "$50.00", "13/11/2026"]))


if __name__ == "__main__":
    unittest.main()
