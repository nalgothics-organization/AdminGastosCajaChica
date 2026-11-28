"""Configuración compartida de las pruebas: base de datos SQLite en memoria, limpia en cada test."""

import os

# Debe fijarse antes de importar src.database para no tocar la base real de PostgreSQL
os.environ["DATABASE_URL"] = "sqlite://"
# Las pruebas suben imágenes sintéticas sin texto; tests/test_legibilidad.py activa la revisión con OCR
os.environ["VALIDAR_LEGIBILIDAD"] = "false"

import secrets

import pytest

from src.database import reiniciar_tablas
from src.models.usuario import RolUsuario, UsuarioCreate
from src.seed import crear_usuarios_demo
from src.services.usuario_service import usuario_service

# Contraseña aleatoria en cada corrida: ninguna contraseña queda escrita en las pruebas.
# Se guarda en el entorno para que los módulos que importan tests.conftest usen la misma.
CONTRASENA_PRUEBAS = os.environ.setdefault("CONTRASENA_PRUEBAS", secrets.token_urlsafe(12))

# Residente de otra obra para probar que no se usan solicitudes ajenas
OTRO_RESIDENTE = UsuarioCreate(
    usuario="OTRO-RESIDENTE", nombre="Residente Ajeno", email="otro.residente@cimas.example",
    rol=RolUsuario.RESIDENTE, obra_id="OBRA-SUR-02", contrasena=CONTRASENA_PRUEBAS,
)


@pytest.fixture(autouse=True)
def base_de_datos_limpia():
    """Base vacía con los usuarios de demostración (RESIDENTE-PAU, ADMIN-LAURA, DIR-CARLOS, ...)."""
    reiniciar_tablas()
    crear_usuarios_demo(CONTRASENA_PRUEBAS)
    usuario_service.crear(OTRO_RESIDENTE)
    yield
