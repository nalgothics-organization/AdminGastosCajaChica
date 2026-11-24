"""Configuración compartida de las pruebas: base de datos SQLite en memoria, limpia en cada test."""

import os

# Debe fijarse antes de importar src.database para no tocar la base real de PostgreSQL
os.environ["DATABASE_URL"] = "sqlite://"
# Las pruebas suben imágenes sintéticas sin texto; tests/test_legibilidad.py activa la revisión con OCR
os.environ["VALIDAR_LEGIBILIDAD"] = "false"

import pytest

from src.database import reiniciar_tablas


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    reiniciar_tablas()
    yield
