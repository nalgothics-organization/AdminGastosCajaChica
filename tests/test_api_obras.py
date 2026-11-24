"""Pruebas de los endpoints del catálogo de obras (RF02/HU02): src/api/obras.py.

Se escribieron para subir la cobertura de este archivo, que era la más baja del proyecto (50 %).
"""

import os
import sys
import unittest
from uuid import uuid4

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.main import app


def obra_nueva(**cambios):
    # Un id distinto en cada prueba, porque el catálogo de obras vive en memoria y no se reinicia
    obra = {
        "id": f"OBRA-PRUEBA-{uuid4().hex[:8].upper()}",
        "nombre": "Obra de prueba",
        "partidas": [{"clave": "P-01", "nombre": "Materiales", "monto_presupuestado": "1000.00"}],
    }
    obra.update(cambios)
    return obra


class TestApiObras(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_lista_las_obras_activas_del_catalogo(self):
        respuesta = self.client.get("/api/obras")

        self.assertEqual(respuesta.status_code, 200)
        self.assertIn("OBRA-NORTE-01", [o["id"] for o in respuesta.json()])

    def test_registra_una_obra_y_lista_sus_partidas(self):
        obra = obra_nueva()

        creada = self.client.post("/api/obras", json=obra)
        partidas = self.client.get(f"/api/obras/{obra['id']}/partidas")

        self.assertEqual(creada.status_code, 201)
        self.assertEqual(partidas.status_code, 200)
        self.assertEqual([p["clave"] for p in partidas.json()], ["P-01"])

    def test_no_registra_dos_veces_la_misma_obra(self):
        obra = obra_nueva()
        self.client.post("/api/obras", json=obra)

        repetida = self.client.post("/api/obras", json=obra)

        self.assertEqual(repetida.status_code, 409)

    def test_partidas_de_una_obra_inexistente_responde_404(self):
        respuesta = self.client.get("/api/obras/OBRA-QUE-NO-EXISTE/partidas")

        self.assertEqual(respuesta.status_code, 404)

    def test_borrado_logico_oculta_la_obra_del_listado(self):
        obra = obra_nueva()
        self.client.post("/api/obras", json=obra)

        borrada = self.client.delete(f"/api/obras/{obra['id']}")
        ids = [o["id"] for o in self.client.get("/api/obras").json()]

        self.assertEqual(borrada.status_code, 204)
        self.assertNotIn(obra["id"], ids)

    def test_borrar_una_obra_inexistente_responde_404(self):
        respuesta = self.client.delete("/api/obras/OBRA-QUE-NO-EXISTE")

        self.assertEqual(respuesta.status_code, 404)


if __name__ == "__main__":
    unittest.main()
