"""Tests de RF04/HU04: bloqueo de fondos nuevos por comprobaciones vencidas.
Un residente con fondos aprobados sin comprobar fuera del límite de días no recibe un fondo nuevo,
y la bandeja de autorización muestra el bloqueo junto a su solicitud.
"""

import os
import sys
import unittest
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.solicitud import AprobacionCreate
from src.services.solicitud_service import (
    LIMITE_DIAS_COMPROBACION_DEFAULT,
    SolicitudBloqueadaError,
    SolicitudFondoService,
    solicitud_service,
)
from tests.test_hu07_comprobacion import BaseHU07TestCase
from tests.test_hu16_captura_rapida import RESIDENTE, crear_solicitud_aprobada

OTRO_RESIDENTE = "RESIDENTE-LUIS"
ADMINISTRACION = {
    "autorizador_id": "ADMIN-LAURA",
    "autorizador_nombre": "Laura Méndez",
    "rol_autorizador": "Administración",
}
PAYLOAD_SOLICITUD = {
    "obra_id": "OBRA-NORTE-01",
    "solicitante_id": RESIDENTE,
    "etapa_construccion": "cimentación",
    "partida_categoria": "Renta de Maquinaria",
    "concepto": "Renta de retroexcavadora para sondeo",
    "monto_solicitado": "3500.00",
    "costo_estimado": "4000.00",
    "urgencia": "urgente",
    "evidencia_url": "https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
}


class BaseBloqueoTestCase(BaseHU07TestCase):
    def avanzar_dias(self, dias):
        """Simula que pasaron `dias` desde ahora para las comprobaciones pendientes."""
        futuro = datetime.now(timezone.utc) + timedelta(days=dias)
        solicitud_service.reloj = lambda: futuro

    def pedir_fondo(self, solicitante=RESIDENTE):
        return self.client.post("/api/solicitudes", json={**PAYLOAD_SOLICITUD, "solicitante_id": solicitante})

    def aprobar(self, solicitud_id):
        return self.client.post(f"/api/solicitudes/{solicitud_id}/aprobar", json=ADMINISTRACION)

    def comprobar(self, monto):
        """Captura, completa y cierra un comprobante de la solicitud aprobada en `self.solicitud`."""
        comprobante_id = self.capturar().json()["id"]
        self.assertEqual(self.completar(comprobante_id, tipo="factura", monto_comprobado=monto).status_code, 200)
        self.assertEqual(self.cerrar(comprobante_id).status_code, 200)
        return comprobante_id


class TestHU04Bloqueo(BaseBloqueoTestCase):
    def test_criterio_1_no_se_aprueba_fondo_nuevo_con_comprobacion_vencida(self):
        """Dado que un residente tiene comprobaciones vencidas, cuando pide un nuevo fondo,
        entonces el sistema no permite autorizarlo."""
        vencida = crear_solicitud_aprobada()
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        response = self.aprobar(nueva_id)

        self.assertEqual(response.status_code, 423)
        self.assertIn(vencida.folio, response.json()["detail"])
        self.assertEqual(self.client.get(f"/api/solicitudes/{nueva_id}").json()["estado"], "Pendiente")

    def test_servicio_tambien_impide_aprobar(self):
        crear_solicitud_aprobada()
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        with self.assertRaises(SolicitudBloqueadaError):
            solicitud_service.aprobar_solicitud(UUID(nueva_id), AprobacionCreate(**ADMINISTRACION))

    def test_criterio_2_residente_es_notificado_al_pedir_fondo(self):
        """Dado que el sistema bloquea la entrega, cuando el residente revisa el estado,
        entonces se le notifica que debe comprobar sus gastos anteriores primero."""
        crear_solicitud_aprobada()
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        creada = self.pedir_fondo().json()["solicitud"]
        consultada = self.client.get(f"/api/solicitudes/{creada['id']}").json()

        for solicitud in (creada, consultada):
            self.assertTrue(solicitud["bloqueo"]["bloqueada"])
            self.assertIn("comprobar sus gastos anteriores", solicitud["bloqueo"]["mensaje"])

    def test_criterio_3_bandeja_marca_bloqueada_con_numero_de_comprobaciones(self):
        """Dado que reviso las autorizaciones en la pantalla única, cuando un residente tiene
        comprobaciones vencidas, entonces su solicitud aparece bloqueada con el número de pendientes."""
        primera = crear_solicitud_aprobada()
        segunda = crear_solicitud_aprobada()
        self.pedir_fondo()
        self.pedir_fondo(solicitante=OTRO_RESIDENTE)
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        pendientes = [s for s in self.client.get("/api/solicitudes").json() if s["estado"] == "Pendiente"]
        bloqueo = {s["solicitante_id"]: s["bloqueo"] for s in pendientes}

        self.assertTrue(bloqueo[RESIDENTE]["bloqueada"])
        self.assertEqual(bloqueo[RESIDENTE]["comprobaciones_vencidas"], 2)
        self.assertEqual(set(bloqueo[RESIDENTE]["folios_vencidos"]), {primera.folio, segunda.folio})
        self.assertEqual(Decimal(bloqueo[RESIDENTE]["monto_por_comprobar"]), Decimal("7000.00"))
        self.assertFalse(bloqueo[OTRO_RESIDENTE]["bloqueada"])

    def test_solicitudes_decididas_no_llevan_bloqueo(self):
        crear_solicitud_aprobada()
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        aprobadas = [s for s in self.client.get("/api/solicitudes").json() if s["estado"] == "Aprobado"]

        self.assertTrue(aprobadas)
        self.assertTrue(all(s["bloqueo"] is None for s in aprobadas))


class TestHU04LimiteDeAntiguedad(BaseBloqueoTestCase):
    def test_dentro_del_limite_si_se_aprueba(self):
        crear_solicitud_aprobada()
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT - 1)

        response = self.aprobar(nueva_id)

        self.assertEqual(response.status_code, 200)

    def test_fondo_comprobado_completo_no_bloquea(self):
        self.solicitud = crear_solicitud_aprobada()
        self.comprobar("3500.00")
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.aprobar(nueva_id).status_code, 200)

    def test_comprobacion_parcial_sigue_bloqueando_por_el_faltante(self):
        self.solicitud = crear_solicitud_aprobada()
        self.comprobar("1000.00")
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        bloqueo = solicitud_service.bloqueo_de(RESIDENTE)

        self.assertTrue(bloqueo.bloqueada)
        self.assertEqual(bloqueo.monto_por_comprobar, Decimal("2500.00"))

    def test_comprobante_en_borrador_no_cuenta_como_comprobado(self):
        self.solicitud = crear_solicitud_aprobada()
        comprobante_id = self.capturar().json()["id"]
        self.completar(comprobante_id, tipo="factura", monto_comprobado="3500.00")
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertTrue(solicitud_service.bloqueo_de(RESIDENTE).bloqueada)

    def test_reverso_reabre_la_comprobacion_pendiente(self):
        self.solicitud = crear_solicitud_aprobada()
        comprobante_id = self.comprobar("3500.00")
        reverso = self.client.post(
            f"/api/comprobantes/{comprobante_id}/ajustes",
            json={"tipo_registro": "reverso", "motivo": "Factura cancelada por el proveedor"},
        )
        self.assertEqual(reverso.status_code, 201)
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertTrue(solicitud_service.bloqueo_de(RESIDENTE).bloqueada)

    def test_bloqueo_es_por_residente(self):
        crear_solicitud_aprobada(solicitante=OTRO_RESIDENTE)
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.aprobar(nueva_id).status_code, 200)

    def test_rechazar_sigue_permitido_aunque_este_bloqueada(self):
        crear_solicitud_aprobada()
        nueva_id = self.pedir_fondo().json()["solicitud"]["id"]
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        response = self.client.post(
            f"/api/solicitudes/{nueva_id}/rechazar",
            json={**ADMINISTRACION, "comentario": "Primero debe comprobar sus gastos anteriores."},
        )

        self.assertEqual(response.status_code, 200)


class TestHU04Configuracion(unittest.TestCase):
    def tearDown(self):
        os.environ.pop("LIMITE_DIAS_COMPROBACION", None)

    def test_limite_se_lee_del_entorno(self):
        os.environ["LIMITE_DIAS_COMPROBACION"] = "15"

        self.assertEqual(SolicitudFondoService().limite_dias_comprobacion, 15)

    def test_limite_por_defecto(self):
        self.assertEqual(SolicitudFondoService().limite_dias_comprobacion, LIMITE_DIAS_COMPROBACION_DEFAULT)

    def test_limite_invalido_o_negativo_falla_al_arrancar(self):
        for valor in ("siete", "-1"):
            os.environ["LIMITE_DIAS_COMPROBACION"] = valor
            with self.assertRaises(ValueError):
                SolicitudFondoService()


if __name__ == "__main__":
    unittest.main()
