"""Tests de los endpoints REST y de la documentación Swagger/OpenAPI.
Cubre todos los endpoints expuestos por la API.
"""

import os
import sys
import unittest
from uuid import uuid4

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient

from src.main import app
from src.services.solicitud_service import solicitud_service


class BaseApiTestCase(unittest.TestCase):
    def setUp(self):
        # Reiniciar el almacén en memoria del singleton para aislar cada test
        solicitud_service.__init__()
        self.client = TestClient(app)
        self.payload_valido = {
            "obra_id": "OBRA-NORTE-01",
            "solicitante_id": "RESIDENTE-PAU",
            "etapa_construccion": "cimentación",
            "partida_categoria": "Renta de Maquinaria",
            "concepto": "Renta de retroexcavadora por hora y media para sondeo",
            "monto_solicitado": "3500.00",
            "costo_estimado": "4000.00",
            "urgencia": "urgente",
            "evidencia_url": "https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
        }

    def crear_solicitud(self, **cambios):
        payload = {**self.payload_valido, **cambios}
        return self.client.post("/api/solicitudes", json=payload)


class TestHealthCheck(BaseApiTestCase):
    def test_get_root_responde_ok(self):
        response = self.client.get("/")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["status"], "ok")


class TestRegistrarSolicitudEndpoint(BaseApiTestCase):
    def test_post_crea_solicitud_y_notifica_administracion(self):
        response = self.crear_solicitud()

        self.assertEqual(response.status_code, 201)
        body = response.json()
        self.assertTrue(body["solicitud"]["folio"].startswith("SOL-OBRA-"))
        self.assertEqual(body["solicitud"]["estado"], "Pendiente")
        self.assertTrue(body["solicitud"]["activo"])
        self.assertEqual(body["notificacion_enviada"]["destinatario_rol"], "Administración")

    def test_post_monto_alto_con_firma_notifica_direccion(self):
        response = self.crear_solicitud(
            monto_solicitado="18000.00",
            firma_digital_direccion="FIRMA-DIR-001",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["notificacion_enviada"]["destinatario_rol"], "Dirección")

    def test_post_monto_alto_sin_firma_devuelve_422(self):
        response = self.crear_solicitud(monto_solicitado="18000.00")

        self.assertEqual(response.status_code, 422)
        self.assertIn("firma digital", response.json()["detail"])

    def test_post_sin_evidencia_devuelve_422(self):
        response = self.crear_solicitud(evidencia_url="     ")

        self.assertEqual(response.status_code, 422)

    def test_post_monto_no_positivo_devuelve_422(self):
        response = self.crear_solicitud(monto_solicitado="0")

        self.assertEqual(response.status_code, 422)

    def test_post_etapa_invalida_devuelve_422(self):
        response = self.crear_solicitud(etapa_construccion="demolición")

        self.assertEqual(response.status_code, 422)

    def test_post_folios_son_unicos(self):
        folio_1 = self.crear_solicitud().json()["solicitud"]["folio"]
        folio_2 = self.crear_solicitud().json()["solicitud"]["folio"]

        self.assertNotEqual(folio_1, folio_2)


class TestListarSolicitudesEndpoint(BaseApiTestCase):
    def test_get_lista_vacia(self):
        response = self.client.get("/api/solicitudes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), [])

    def test_get_lista_solo_solicitudes_activas(self):
        id_activa = self.crear_solicitud().json()["solicitud"]["id"]
        id_borrada = self.crear_solicitud().json()["solicitud"]["id"]
        self.client.delete(f"/api/solicitudes/{id_borrada}")

        response = self.client.get("/api/solicitudes")

        self.assertEqual(response.status_code, 200)
        self.assertEqual([s["id"] for s in response.json()], [id_activa])


class TestObtenerSolicitudEndpoint(BaseApiTestCase):
    def test_get_por_id_existente(self):
        creada = self.crear_solicitud().json()["solicitud"]

        response = self.client.get(f"/api/solicitudes/{creada['id']}")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["folio"], creada["folio"])

    def test_get_por_id_inexistente_devuelve_404(self):
        response = self.client.get(f"/api/solicitudes/{uuid4()}")

        self.assertEqual(response.status_code, 404)

    def test_get_por_id_invalido_devuelve_422(self):
        response = self.client.get("/api/solicitudes/no-es-un-uuid")

        self.assertEqual(response.status_code, 422)


class TestEliminarSolicitudEndpoint(BaseApiTestCase):
    def test_delete_realiza_soft_delete(self):
        solicitud_id = self.crear_solicitud().json()["solicitud"]["id"]

        response = self.client.delete(f"/api/solicitudes/{solicitud_id}")

        self.assertEqual(response.status_code, 204)
        self.assertEqual(self.client.get(f"/api/solicitudes/{solicitud_id}").status_code, 404)
        # El registro se conserva para auditoría (AGENTS.md Sección 8)
        registro = next(s for s in solicitud_service._db.values() if str(s.id) == solicitud_id)
        self.assertFalse(registro.activo)
        self.assertIsNotNone(registro.deleted_at)

    def test_delete_dos_veces_devuelve_404(self):
        solicitud_id = self.crear_solicitud().json()["solicitud"]["id"]
        self.client.delete(f"/api/solicitudes/{solicitud_id}")

        response = self.client.delete(f"/api/solicitudes/{solicitud_id}")

        self.assertEqual(response.status_code, 404)

    def test_delete_inexistente_devuelve_404(self):
        response = self.client.delete(f"/api/solicitudes/{uuid4()}")

        self.assertEqual(response.status_code, 404)


class TestSwaggerDocumentacion(BaseApiTestCase):
    ENDPOINTS_ESPERADOS = {
        ("get", "/"),
        ("post", "/api/solicitudes"),
        ("get", "/api/solicitudes"),
        ("get", "/api/solicitudes/{solicitud_id}"),
        ("delete", "/api/solicitudes/{solicitud_id}"),
    }

    def setUp(self):
        super().setUp()
        self.openapi = self.client.get("/openapi.json").json()

    def test_swagger_ui_y_redoc_disponibles(self):
        self.assertEqual(self.client.get("/docs").status_code, 200)
        self.assertEqual(self.client.get("/redoc").status_code, 200)
        self.assertEqual(self.client.get("/openapi.json").status_code, 200)

    def test_todos_los_endpoints_estan_documentados(self):
        documentados = {
            (metodo, ruta)
            for ruta, operaciones in self.openapi["paths"].items()
            for metodo in operaciones
        }

        self.assertEqual(documentados, self.ENDPOINTS_ESPERADOS)

    def test_cada_endpoint_tiene_summary_y_tag(self):
        for metodo, ruta in self.ENDPOINTS_ESPERADOS:
            operacion = self.openapi["paths"][ruta][metodo]
            with self.subTest(endpoint=f"{metodo.upper()} {ruta}"):
                self.assertTrue(operacion.get("summary"))
                self.assertTrue(operacion.get("tags"))

    def test_endpoints_por_id_documentan_404(self):
        for metodo in ("get", "delete"):
            operacion = self.openapi["paths"]["/api/solicitudes/{solicitud_id}"][metodo]
            with self.subTest(metodo=metodo):
                self.assertIn("404", operacion["responses"])

    def test_registro_incluye_ejemplo_de_payload(self):
        esquema = self.openapi["components"]["schemas"]["SolicitudFondoCreate"]

        self.assertTrue(esquema.get("examples"))


if __name__ == "__main__":
    unittest.main()
