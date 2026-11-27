"""Tests del script de creación de tablas (python -m src.crear_tablas)."""

import io
import os
import sys
import unittest
from contextlib import redirect_stdout

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import inspect

from src import crear_tablas
from src.database import engine
from src.services.solicitud_service import solicitud_service


class TestCrearTablas(unittest.TestCase):
    def test_crea_las_tablas_con_borrado_logico(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            crear_tablas.main()

        tablas = set(inspect(engine).get_table_names())
        self.assertTrue({"usuarios", "solicitudes", "autorizaciones", "comprobantes"} <= tablas)
        for tabla in ("usuarios", "solicitudes", "comprobantes"):
            with self.subTest(tabla=tabla):
                columnas = {c["name"] for c in inspect(engine).get_columns(tabla)}
                self.assertIn("deleted_at", columnas)
                self.assertIn(f"{tabla}:", salida.getvalue())

    def test_volver_a_ejecutarlo_no_borra_datos(self):
        antes = len(solicitud_service.listar_solicitudes_activas())
        with redirect_stdout(io.StringIO()):
            crear_tablas.main()
            crear_tablas.main()
        self.assertEqual(len(solicitud_service.listar_solicitudes_activas()), antes)

    def test_no_muestra_la_contrasena_de_la_conexion(self):
        salida = io.StringIO()
        with redirect_stdout(salida):
            crear_tablas.main()
        if engine.url.password:
            self.assertNotIn(engine.url.password, salida.getvalue())


if __name__ == "__main__":
    unittest.main()
