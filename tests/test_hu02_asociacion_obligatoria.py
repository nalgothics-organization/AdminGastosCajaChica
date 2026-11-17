"""Tests unitarios para HU02 y RF02.
Todo gasto debe asociarse a una obra activa, una etapa de construcción y una partida presupuestal;
no se permiten gastos genéricos ni sin obra.
"""

import os
import sys
from decimal import Decimal
import unittest

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pydantic import ValidationError

from src.models.obra import EstadoObra, Obra, PartidaPresupuestal
from src.models.solicitud import (
    EtapaConstruccion,
    SolicitudFondoCreate,
    UrgenciaSolicitud,
)
from src.services.obra_service import ObraService
from src.services.solicitud_service import SolicitudFondoService


class TestHU02AsociacionObligatoria(unittest.TestCase):
    def setUp(self):
        self.obra_service = ObraService()
        self.obra_service.registrar_obra(
            Obra(
                id="OBRA-NORTE-01",
                nombre="Residencial Norte",
                partidas=[PartidaPresupuestal(clave="P-01", nombre="Renta de Maquinaria")],
            )
        )
        self.obra_service.registrar_obra(
            Obra(
                id="OBRA-SUR-02",
                nombre="Plaza Sur",
                partidas=[PartidaPresupuestal(clave="P-01", nombre="Acero de Refuerzo")],
            )
        )
        self.obra_service.registrar_obra(
            Obra(
                id="OBRA-CERR-03",
                nombre="Casa Cerrada",
                estado=EstadoObra.CERRADA,
                partidas=[PartidaPresupuestal(clave="P-01", nombre="Renta de Maquinaria")],
            )
        )
        self.service = SolicitudFondoService(obra_service=self.obra_service)
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

    def _payload(self, **cambios):
        payload = self.payload_valido.copy()
        payload.update(cambios)
        return payload

    def test_criterio_1_rechaza_gasto_sin_obra_o_con_obra_inactiva(self):
        """Criterio 1: si se omite la obra o no está activa, el sistema bloquea el envío."""
        payload_sin_obra = self.payload_valido.copy()
        del payload_sin_obra["obra_id"]
        with self.assertRaises(ValidationError):
            SolicitudFondoCreate(**payload_sin_obra)
        with self.assertRaises(ValidationError):
            SolicitudFondoCreate(**self._payload(obra_id="   "))

        self.obra_service.soft_delete("OBRA-SUR-02")
        for obra_id in ("OBRA-INEXISTENTE", "OBRA-CERR-03", "OBRA-SUR-02"):
            with self.assertRaises(ValueError, msg=obra_id):
                self.service.crear_solicitud(SolicitudFondoCreate(**self._payload(obra_id=obra_id)))

    def test_criterio_2_etapa_y_partida_obligatorias_sin_gastos_genericos(self):
        """Criterio 2 / RF02: la etapa y la partida son obligatorias y no se permiten gastos genéricos."""
        for campo in ("etapa_construccion", "partida_categoria"):
            payload = self.payload_valido.copy()
            del payload[campo]
            with self.assertRaises(ValidationError, msg=campo):
                SolicitudFondoCreate(**payload)

        with self.assertRaises(ValidationError):
            SolicitudFondoCreate(**self._payload(etapa_construccion="general"))
        for valor in ("", "Varios", " otros ", "GENERAL"):
            with self.assertRaises(ValidationError, msg=valor):
                SolicitudFondoCreate(**self._payload(partida_categoria=valor))
        with self.assertRaises(ValidationError):
            PartidaPresupuestal(clave="P-99", nombre="Misceláneos")

    def test_partida_debe_pertenecer_al_presupuesto_de_la_obra(self):
        with self.assertRaises(ValueError) as ctx:
            self.service.crear_solicitud(
                SolicitudFondoCreate(**self._payload(partida_categoria="Acero de Refuerzo"))
            )
        self.assertIn("no pertenece al presupuesto", str(ctx.exception))

    def test_criterio_4_asocia_costo_a_obra_etapa_y_partida(self):
        """Criterios 3 y 4: se registra el gasto asociado a la obra, la etapa y la partida seleccionadas."""
        resultado = self.service.crear_solicitud(
            SolicitudFondoCreate(
                **self._payload(
                    obra_id=" obra-norte-01 ",
                    partida_categoria="  renta de   MAQUINARIA ",
                    etapa_construccion=EtapaConstruccion.ESTRUCTURA,
                )
            )
        )
        solicitud = resultado.solicitud

        self.assertEqual(solicitud.obra_id, "OBRA-NORTE-01")
        self.assertEqual(solicitud.etapa_construccion, EtapaConstruccion.ESTRUCTURA)
        self.assertEqual(solicitud.partida_categoria, "Renta de Maquinaria")
        self.assertEqual(solicitud.costo_estimado, Decimal("4000.00"))
        self.assertEqual(solicitud.monto_solicitado, Decimal("3500.00"))


if __name__ == "__main__":
    unittest.main()
