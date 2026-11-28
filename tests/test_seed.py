"""Tests de los datos de ejemplo: deben poder cargarse con las reglas actuales del flujo."""

import tempfile
import unittest

from src import seed
from src.services.comprobante_service import comprobante_service
from src.services.solicitud_service import solicitud_service


class TestSeed(unittest.TestCase):
    def test_los_datos_de_ejemplo_se_cargan_completos(self):
        with tempfile.TemporaryDirectory() as carpeta:
            solicitud_service.__init__()
            comprobante_service.__init__(uploads_dir=carpeta)

            seed.cargar()

            solicitudes = solicitud_service.listar_solicitudes_activas()
            self.assertEqual(len(solicitudes), 6)
            entregadas = [s for s in solicitudes if s.entrega]
            por_entregar = [s for s in solicitudes if s.estado.value == "Aprobado" and not s.entrega]
            self.assertEqual(len(entregadas), 2)
            self.assertEqual(len(por_entregar), 1)
            self.assertEqual(len(comprobante_service.listar()), 4)
            vinculados = [c for c in comprobante_service.listar() if c.solicitud_id]
            self.assertEqual(len(vinculados), 2)


if __name__ == "__main__":
    unittest.main()
