"""Tests del catálogo de obras: el fondo de caja chica baja al aprobar solicitudes."""

import unittest
from decimal import Decimal

from fastapi.testclient import TestClient
from src.main import app
from tests.test_hu16_captura_rapida import crear_solicitud_aprobada


class TestCatalogoObras(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def obra(self, obra_id):
        obras = self.client.get("/api/catalogo/obras").json()
        return next(o for o in obras if o["id"] == obra_id)

    def test_sin_aprobaciones_el_disponible_es_todo_el_fondo(self):
        obra = self.obra("OBRA-NORTE-01")

        self.assertEqual(Decimal(obra["disponible_caja_chica"]), Decimal(obra["presupuesto_caja_chica"]))
        self.assertEqual(Decimal(obra["autorizado"]), Decimal("0"))

    def test_aprobar_una_solicitud_descuenta_su_monto_del_fondo_de_su_obra(self):
        antes = Decimal(self.obra("OBRA-NORTE-01")["disponible_caja_chica"])

        crear_solicitud_aprobada()

        despues = self.obra("OBRA-NORTE-01")
        self.assertEqual(Decimal(despues["disponible_caja_chica"]), antes - Decimal("3500.00"))
        self.assertEqual(Decimal(despues["autorizado"]), Decimal("3500.00"))
        self.assertEqual(Decimal(self.obra("OBRA-SUR-02")["autorizado"]), Decimal("0"))
