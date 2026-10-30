"""Configuración compartida de las pruebas: base de datos SQLite en memoria, limpia en cada test."""

import os

# Debe fijarse antes de importar src.database para no tocar la base real de PostgreSQL
os.environ["DATABASE_URL"] = "sqlite://"

import pytest

from src.database import reiniciar_tablas


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    reiniciar_tablas()
    yield
