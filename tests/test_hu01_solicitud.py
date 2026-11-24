"""Tests unitarios e integración para HU01 y RF01.
Validación de criterios de aceptación de HU01 y reglas de negocio de AGENTS.md.
"""

import os
import sys
from decimal import Decimal
import unittest

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from src.models.solicitud import (
    EtapaConstruccion,
    SolicitudFondoCreate,
    UrgenciaSolicitud,
)
from src.models.obra import Obra, PartidaPresupuestal
from src.services.obra_service import ObraService
from src.services.solicitud_service import SolicitudFondoService


class TestHU01RegistroSolicitudFondo(unittest.TestCase):
    def setUp(self):
        obra_service = ObraService()
        obra_service.registrar_obra(
            Obra(
                id="OBRA-NORTE-01",
                nombre="Residencial Norte",
                partidas=[PartidaPresupuestal(clave="P-01", nombre="Renta de Maquinaria")],
            )
        )
        self.service = SolicitudFondoService(obra_service=obra_service)
        self.payload_valido = {
            "obra_id": "OBRA-NORTE-01",
            "solicitante_id": "RESIDENTE-PAU",
            "etapa_construccion": EtapaConstruccion.CIMENTACION,
            "partida_categoria": "Renta de Maquinaria",
            "concepto": "Renta de retroexcavadora por hora y media para sondeo",
            "monto_solicitado": Decimal("3500.00"),
            "costo_estimado": Decimal("4000.00"),
            "urgencia": UrgenciaSolicitud.URGENTE,
            "evidencia_url": "https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
        }

    def test_criterio_1_solicitud_rechazada_si_falta_evidencia(self):
        """Criterio 1: Dado que necesito un material urgente, cuando ingreso una solicitud,
        entonces el sistema me pide adjuntar una evidencia de la necesidad.
        """
        payload_sin_evidencia = self.payload_valido.copy()
        payload_sin_evidencia["evidencia_url"] = ""

        # Validación a nivel Pydantic / Validación de Dominio
        with self.assertRaises(ValidationError):
            SolicitudFondoCreate(**payload_sin_evidencia)

        payload_espacios = self.payload_valido.copy()
        payload_espacios["evidencia_url"] = "   "
        with self.assertRaises(ValidationError):
            SolicitudFondoCreate(**payload_espacios)

    def test_criterio_2_generacion_folio_unico_y_notificacion_administracion(self):
        """Criterio 2: Dado que completo la solicitud, cuando la envío,
        entonces se genera un folio único y se notifica al nivel de autorización correspondiente.
        (Monto menor a 5,000 -> Administración)
        """
        data_create = SolicitudFondoCreate(**self.payload_valido)
        resultado = self.service.crear_solicitud(data_create)

        solicitud = resultado.solicitud
        notificacion = resultado.notificacion_enviada

        # Verifica generación de folio único y legible
        self.assertTrue(solicitud.folio.startswith("SOL-OBRA-"))
        self.assertEqual(solicitud.estado, "Pendiente")
        self.assertTrue(solicitud.activo)

        # Verifica notificación al nivel correspondiente (Administración)
        self.assertEqual(notificacion.destinatario_rol, "Administración")
        self.assertEqual(notificacion.folio, solicitud.folio)
        self.assertIn("Administración", notificacion.mensaje)
        self.assertIn(notificacion, self.service.notificaciones_enviadas)

    def test_criterio_2_notificacion_escala_a_direccion_para_montos_altos(self):
        """Criterio 2: Si el monto solicitado supera el umbral de administración (> 5,000 MXN),
        se escala y notifica al nivel correspondiente (Dirección).
        """
        payload_monto_alto = self.payload_valido.copy()
        payload_monto_alto["monto_solicitado"] = Decimal("18000.00")
        payload_monto_alto["firma_digital_direccion"] = "FIRMA-DIR-001"

        data_create = SolicitudFondoCreate(**payload_monto_alto)
        resultado = self.service.crear_solicitud(data_create)

        self.assertEqual(resultado.notificacion_enviada.destinatario_rol, "Dirección")
        self.assertIn("Dirección", resultado.notificacion_enviada.mensaje)
        self.assertEqual(resultado.solicitud.firma_digital_direccion, "FIRMA-DIR-001")

    def test_monto_alto_sin_firma_de_direccion_es_rechazado(self):
        """Niveles escalonados: montos mayores a 5,000 MXN requieren firma digital de Dirección."""
        payload_monto_alto = self.payload_valido.copy()
        payload_monto_alto["monto_solicitado"] = Decimal("18000.00")

        data_create = SolicitudFondoCreate(**payload_monto_alto)
        with self.assertRaises(ValueError):
            self.service.crear_solicitud(data_create)

        self.assertEqual(self.service.listar_solicitudes_activas(), [])
        self.assertEqual(self.service.notificaciones_enviadas, [])

    def test_monto_en_el_limite_se_notifica_a_administracion(self):
        """Exactamente 5,000 MXN sigue dentro del límite de Administración."""
        payload_limite = self.payload_valido.copy()
        payload_limite["monto_solicitado"] = Decimal("5000.00")

        resultado = self.service.crear_solicitud(SolicitudFondoCreate(**payload_limite))

        self.assertEqual(resultado.notificacion_enviada.destinatario_rol, "Administración")

    def test_regla_negocio_soft_delete(self):
        """Regla de negocio AGENTS.md Sección 8:
        Prohibido hard delete, solo soft delete.
        """
        data_create = SolicitudFondoCreate(**self.payload_valido)
        resultado = self.service.crear_solicitud(data_create)
        solicitud_id = resultado.solicitud.id

        # Ejecutar soft delete
        borrado = self.service.soft_delete(solicitud_id)
        self.assertTrue(borrado)

        # La solicitud ya no debe aparecer como activa en consultas ordinarias
        self.assertIsNone(self.service.obtener_por_id(solicitud_id))
        self.assertNotIn(solicitud_id, [s.id for s in self.service.listar_solicitudes_activas()])

        # En la base interna sigue existiendo para auditoría con deleted_at marcado
        registro_interno = self.service._db[solicitud_id]
        self.assertFalse(registro_interno.activo)
        self.assertIsNotNone(registro_interno.deleted_at)


if __name__ == "__main__":
    unittest.main()
