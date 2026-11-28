"""Tests del modelo y el servicio de usuarios (base de RF15/HU20).
Cubre el alta, la autenticación básica, la baja lógica y el uso del rol en solicitudes y comprobantes.
"""

import os
import sys
import unittest
from unittest import mock

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from pydantic import ValidationError

from src import seed
from src.main import app
from src.models.usuario import RolUsuario, UsuarioCreate
from src.repositories import UsuarioRepositorio
from src.services.usuario_service import (
    RolNoPermitidoError,
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
    usuario_service,
)
from tests.conftest import CONTRASENA_PRUEBAS
from tests.test_hu16_captura_rapida import JPEG_VALIDO

NUEVO = {
    "usuario": "  conta-ana ",
    "nombre": "Ana Gómez",
    "email": "Ana.Gomez@Cimas.Example",
    "rol": RolUsuario.CONTABILIDAD,
    "contrasena": "contrasena-de-prueba",
}
SOLICITUD = {
    "obra_id": "OBRA-NORTE-01",
    "solicitante_id": "RESIDENTE-PAU",
    "etapa_construccion": "cimentación",
    "partida_categoria": "Materiales",
    "concepto": "Compra de cemento",
    "monto_solicitado": "1000.00",
    "costo_estimado": "1000.00",
    "urgencia": "media",
    "evidencia_url": "https://storage.empresa.com/evidencias/cemento.jpg",
}


class TestModeloUsuario(unittest.TestCase):
    def test_normaliza_usuario_y_correo(self):
        usuario = usuario_service.crear(UsuarioCreate(**NUEVO))

        self.assertEqual(usuario.usuario, "CONTA-ANA")
        self.assertEqual(usuario.email, "ana.gomez@cimas.example")
        self.assertTrue(usuario.activo)

    def test_la_contrasena_nunca_se_serializa(self):
        usuario = usuario_service.crear(UsuarioCreate(**NUEVO))

        self.assertNotIn("contrasena", usuario.model_dump())
        self.assertNotIn(NUEVO["contrasena"], usuario.model_dump_json())
        self.assertNotIn(NUEVO["contrasena"], repr(usuario))
        self.assertNotIn("contrasena", usuario.publico().model_dump())

    def test_datos_invalidos(self):
        casos = {
            "usuario corto": {"usuario": "ab"},
            "usuario con espacios": {"usuario": "ana gomez"},
            "correo inválido": {"email": "ana-sin-arroba"},
            "contraseña corta": {"contrasena": "1234"},
            "nombre corto": {"nombre": "A"},
            "rol desconocido": {"rol": "Gerencia"},
        }
        for caso, cambio in casos.items():
            with self.subTest(caso=caso), self.assertRaises(ValidationError):
                UsuarioCreate(**{**NUEVO, **cambio})

    def test_residente_requiere_obra_existente(self):
        with self.assertRaises(ValidationError):
            UsuarioCreate(**{**NUEVO, "rol": RolUsuario.RESIDENTE})
        with self.assertRaises(ValueError):
            usuario_service.crear(UsuarioCreate(**{**NUEVO, "rol": RolUsuario.RESIDENTE, "obra_id": "OBRA-X"}))

        residente = usuario_service.crear(
            UsuarioCreate(**{**NUEVO, "rol": RolUsuario.RESIDENTE, "obra_id": "OBRA-SUR-02"})
        )
        self.assertEqual(residente.obra_id, "OBRA-SUR-02")


class TestServicioUsuario(unittest.TestCase):
    def test_usuario_y_correo_no_se_repiten(self):
        usuario_service.crear(UsuarioCreate(**NUEVO))

        for cambio in ({"email": "otra@cimas.example"}, {"usuario": "OTRA-ANA"}):
            with self.subTest(cambio=cambio), self.assertRaises(UsuarioDuplicadoError):
                usuario_service.crear(UsuarioCreate(**{**NUEVO, **cambio}))

    def test_autenticar(self):
        usuario_service.crear(UsuarioCreate(**NUEVO))

        self.assertEqual(usuario_service.autenticar("conta-ana", NUEVO["contrasena"]).usuario, "CONTA-ANA")
        self.assertIsNone(usuario_service.autenticar("CONTA-ANA", "otra-contrasena"))
        self.assertIsNone(usuario_service.autenticar("CONTA-ANA", ""))
        self.assertIsNone(usuario_service.autenticar("NADIE", NUEVO["contrasena"]))

    def test_usuarios_demo_inician_sesion_con_la_contrasena_de_pruebas(self):
        self.assertIsNotNone(usuario_service.autenticar("ADMIN-LAURA", CONTRASENA_PRUEBAS))

    def test_cambiar_contrasena(self):
        usuario = usuario_service.crear(UsuarioCreate(**NUEVO))

        with self.assertRaises(ValueError):
            usuario_service.cambiar_contrasena(usuario.id, "incorrecta", "nueva-contrasena")
        with self.assertRaises(ValueError):
            usuario_service.cambiar_contrasena(usuario.id, NUEVO["contrasena"], "corta")
        usuario_service.cambiar_contrasena(usuario.id, NUEVO["contrasena"], "nueva-contrasena")

        self.assertIsNone(usuario_service.autenticar("CONTA-ANA", NUEVO["contrasena"]))
        self.assertIsNotNone(usuario_service.autenticar("CONTA-ANA", "nueva-contrasena"))

    def test_desactivar_es_baja_logica(self):
        usuario = usuario_service.crear(UsuarioCreate(**NUEVO))

        self.assertTrue(usuario_service.desactivar(usuario.id))
        self.assertFalse(usuario_service.desactivar(usuario.id))

        # El registro se conserva para la auditoría, pero ya no inicia sesión ni se reutiliza
        guardado = UsuarioRepositorio().get(usuario.id)
        self.assertFalse(guardado.activo)
        self.assertIsNotNone(guardado.deleted_at)
        self.assertIsNone(usuario_service.obtener_por_id(usuario.id))
        self.assertIsNone(usuario_service.autenticar("CONTA-ANA", NUEVO["contrasena"]))
        with self.assertRaises(UsuarioDuplicadoError):
            usuario_service.crear(UsuarioCreate(**NUEVO))

    def test_listar_por_rol(self):
        residentes = {u.usuario for u in usuario_service.listar(RolUsuario.RESIDENTE)}

        self.assertEqual(residentes, {"RESIDENTE-PAU", "RESIDENTE-JP", "RESIDENTE-LUIS", "OTRO-RESIDENTE"})
        self.assertEqual(len(usuario_service.listar()), 7)

    def test_exigir_rol(self):
        self.assertEqual(
            usuario_service.exigir("admin-laura", [RolUsuario.ADMINISTRACION], "aprobar").nombre, "Laura Méndez"
        )
        with self.assertRaises(RolNoPermitidoError):
            usuario_service.exigir("CONT-SOFIA", [RolUsuario.ADMINISTRACION], "aprobar")
        with self.assertRaises(UsuarioNoEncontradoError):
            usuario_service.exigir("NADIE", [RolUsuario.ADMINISTRACION], "aprobar")


class TestRolEnSolicitudesYComprobantes(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    def test_solo_un_residente_registra_solicitudes(self):
        admin = self.client.post("/api/solicitudes", json={**SOLICITUD, "solicitante_id": "ADMIN-LAURA"})
        inexistente = self.client.post("/api/solicitudes", json={**SOLICITUD, "solicitante_id": "NADIE"})
        residente = self.client.post("/api/solicitudes", json={**SOLICITUD, "solicitante_id": "residente-pau"})

        self.assertEqual(admin.status_code, 403)
        self.assertEqual(inexistente.status_code, 422)
        self.assertEqual(residente.status_code, 201)
        self.assertEqual(residente.json()["solicitud"]["solicitante_id"], "RESIDENTE-PAU")

    def test_residente_dado_de_baja_no_solicita(self):
        usuario_service.desactivar(usuario_service.obtener_por_usuario("RESIDENTE-PAU").id)

        response = self.client.post("/api/solicitudes", json=SOLICITUD)

        self.assertEqual(response.status_code, 422)

    def test_solo_un_residente_captura_comprobantes(self):
        def capturar(solicitante):
            return self.client.post(
                "/api/comprobantes/captura",
                data={"solicitante_id": solicitante},
                files={"imagen": ("ticket.jpg", JPEG_VALIDO, "image/jpeg")},
            )

        self.assertEqual(capturar("CONT-SOFIA").status_code, 403)
        self.assertEqual(capturar("NADIE").status_code, 422)
        self.assertEqual(capturar("RESIDENTE-PAU").status_code, 201)

    def test_autorizacion_guarda_nombre_y_rol_del_usuario(self):
        solicitud_id = self.client.post("/api/solicitudes", json=SOLICITUD).json()["solicitud"]["id"]

        response = self.client.post(
            f"/api/solicitudes/{solicitud_id}/aprobar",
            json={"autorizador_id": "dir-carlos", "clasificacion": "cobrable_cliente"},
        )

        autorizacion = response.json()["autorizacion"]
        self.assertEqual(autorizacion["autorizador_id"], "DIR-CARLOS")
        self.assertEqual(autorizacion["autorizador_nombre"], "Carlos Ruiz")
        self.assertEqual(autorizacion["rol_autorizador"], "Dirección")


class TestSeedUsuarios(unittest.TestCase):
    def test_crear_usuarios_demo_no_duplica(self):
        self.assertEqual(seed.crear_usuarios_demo(CONTRASENA_PRUEBAS), 0)

    def test_seed_exige_contrasena_demo(self):
        with mock.patch.dict(os.environ, {"CONTRASENA_DEMO": ""}), self.assertRaises(SystemExit):
            seed.main()


if __name__ == "__main__":
    unittest.main()
