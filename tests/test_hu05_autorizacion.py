"""Tests de RF05/HU05: aprobación o rechazo de solicitudes con trazabilidad.
Se registra quién autorizó, cuándo, el monto final y los comentarios.
"""

import os
import sys
import unittest
from decimal import Decimal
from uuid import uuid4

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.solicitud import (
    AprobacionCreate,
    EstadoSolicitud,
    RechazoCreate,
    SolicitudFondoCreate,
)
from src.services.solicitud_service import (
    AutorizadorNoPermitidoError,
    SolicitudFondoService,
    SolicitudNoEncontradaError,
    SolicitudNoPendienteError,
)
from tests.test_api_solicitudes import BaseApiTestCase

ADMINISTRACION = {
    "autorizador_id": "ADMIN-LAURA",
    "clasificacion": "cobrable_cliente",
}
DIRECCION = {
    "autorizador_id": "DIR-CARLOS",
    "clasificacion": "cobrable_cliente",
}
COMENTARIO_RECHAZO = "El gasto no corresponde a la etapa actual de la obra."


class BaseAutorizacionTestCase(BaseApiTestCase):
    def crear_pendiente(self, **cambios):
        return self.crear_solicitud(**cambios).json()["solicitud"]["id"]

    def crear_pendiente_direccion(self):
        return self.crear_pendiente(monto_solicitado="18000.00", firma_digital_direccion="FIRMA-DIR-001")

    def aprobar(self, solicitud_id, **cuerpo):
        return self.client.post(f"/api/solicitudes/{solicitud_id}/aprobar", json={**ADMINISTRACION, **cuerpo})

    def rechazar(self, solicitud_id, **cuerpo):
        return self.client.post(f"/api/solicitudes/{solicitud_id}/rechazar", json={**ADMINISTRACION, **cuerpo})

    def estado_actual(self, solicitud_id):
        return self.client.get(f"/api/solicitudes/{solicitud_id}").json()["estado"]


class TestHU05Aprobacion(BaseAutorizacionTestCase):
    def test_criterio_1_aprobar_registra_nombre_fecha_y_monto_final(self):
        """Dado que tengo una solicitud pendiente, cuando la apruebo,
        entonces queda registrado mi nombre, la fecha y el monto final."""
        solicitud_id = self.crear_pendiente()

        response = self.aprobar(solicitud_id, monto_autorizado="3000.00", comentario="Cotización validada.")

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["estado"], "Aprobado")
        autorizacion = body["autorizacion"]
        self.assertEqual(autorizacion["decision"], "Aprobada")
        self.assertEqual(autorizacion["autorizador_nombre"], "Laura Méndez")
        self.assertEqual(autorizacion["autorizador_id"], "ADMIN-LAURA")
        self.assertEqual(autorizacion["rol_autorizador"], "Administración")
        self.assertEqual(Decimal(autorizacion["monto_autorizado"]), Decimal("3000.00"))
        self.assertEqual(autorizacion["comentario"], "Cotización validada.")
        self.assertTrue(autorizacion["fecha_decision"])

    def test_criterio_1_decision_persiste_al_consultar(self):
        solicitud_id = self.crear_pendiente()
        self.aprobar(solicitud_id)

        body = self.client.get(f"/api/solicitudes/{solicitud_id}").json()

        self.assertEqual(body["estado"], "Aprobado")
        self.assertEqual(body["autorizacion"]["autorizador_nombre"], "Laura Méndez")

    def test_sin_monto_se_autoriza_el_solicitado(self):
        solicitud_id = self.crear_pendiente()

        response = self.aprobar(solicitud_id)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(Decimal(response.json()["autorizacion"]["monto_autorizado"]), Decimal("3500.00"))
        self.assertIsNone(response.json()["autorizacion"]["comentario"])

    def test_monto_mayor_al_solicitado_devuelve_422(self):
        solicitud_id = self.crear_pendiente()

        response = self.aprobar(solicitud_id, monto_autorizado="3500.01")

        self.assertEqual(response.status_code, 422)
        self.assertIn("no puede ser mayor al monto solicitado", response.json()["detail"])
        self.assertEqual(self.estado_actual(solicitud_id), "Pendiente")

    def test_monto_no_positivo_devuelve_422(self):
        solicitud_id = self.crear_pendiente()

        for monto in ("0", "-100.00"):
            with self.subTest(monto=monto):
                response = self.aprobar(solicitud_id, monto_autorizado=monto)
                self.assertEqual(response.status_code, 422)

        self.assertEqual(self.estado_actual(solicitud_id), "Pendiente")


class TestHU05Rechazo(BaseAutorizacionTestCase):
    def test_criterio_2_rechazar_sin_comentario_devuelve_422(self):
        """Dado que rechazo un gasto, cuando confirmo la acción,
        entonces debo ingresar obligatoriamente un comentario justificando la decisión."""
        solicitud_id = self.crear_pendiente()

        for cuerpo in ({}, {"comentario": None}, {"comentario": "   "}, {"comentario": "no"}):
            with self.subTest(cuerpo=cuerpo):
                response = self.rechazar(solicitud_id, **cuerpo)
                self.assertEqual(response.status_code, 422)
                self.assertIn("comentario que justifique el rechazo", str(response.json()["detail"]))

        self.assertEqual(self.estado_actual(solicitud_id), "Pendiente")

    def test_criterio_2_rechazar_con_comentario_registra_decision(self):
        solicitud_id = self.crear_pendiente()

        response = self.rechazar(solicitud_id, comentario=COMENTARIO_RECHAZO)

        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertEqual(body["estado"], "Rechazado")
        autorizacion = body["autorizacion"]
        self.assertEqual(autorizacion["decision"], "Rechazada")
        self.assertEqual(autorizacion["autorizador_nombre"], "Laura Méndez")
        self.assertEqual(autorizacion["comentario"], COMENTARIO_RECHAZO)
        self.assertIsNone(autorizacion["monto_autorizado"])
        self.assertTrue(autorizacion["fecha_decision"])


class TestHU05ReglasDeNegocio(BaseAutorizacionTestCase):
    def test_solicitud_decidida_no_puede_decidirse_de_nuevo(self):
        """AGENTS.md §8: una solicitud aprobada no se modifica directamente."""
        solicitud_id = self.crear_pendiente()
        self.aprobar(solicitud_id, monto_autorizado="3000.00")

        for intento in (
            lambda: self.aprobar(solicitud_id, monto_autorizado="1000.00"),
            lambda: self.rechazar(solicitud_id, comentario=COMENTARIO_RECHAZO),
        ):
            with self.subTest(intento=intento):
                self.assertEqual(intento().status_code, 409)

        body = self.client.get(f"/api/solicitudes/{solicitud_id}").json()
        self.assertEqual(body["estado"], "Aprobado")
        self.assertEqual(Decimal(body["autorizacion"]["monto_autorizado"]), Decimal("3000.00"))

    def test_administracion_no_decide_montos_de_direccion(self):
        solicitud_id = self.crear_pendiente_direccion()

        aprobar = self.aprobar(solicitud_id)
        rechazar = self.rechazar(solicitud_id, comentario=COMENTARIO_RECHAZO)

        self.assertEqual(aprobar.status_code, 403)
        self.assertEqual(rechazar.status_code, 403)
        self.assertEqual(self.estado_actual(solicitud_id), "Pendiente")

    def test_direccion_decide_cualquier_nivel(self):
        alta = self.crear_pendiente_direccion()
        baja = self.crear_pendiente()

        self.assertEqual(self.aprobar(alta, **DIRECCION).status_code, 200)
        self.assertEqual(self.rechazar(baja, **DIRECCION, comentario=COMENTARIO_RECHAZO).status_code, 200)

    def test_solo_administracion_o_direccion_deciden(self):
        """El rol sale del registro del usuario: contabilidad y residentes no deciden solicitudes."""
        solicitud_id = self.crear_pendiente()

        for usuario in ("CONT-SOFIA", "RESIDENTE-JP"):
            with self.subTest(usuario=usuario):
                self.assertEqual(self.aprobar(solicitud_id, autorizador_id=usuario).status_code, 403)
                rechazo = self.rechazar(solicitud_id, autorizador_id=usuario, comentario=COMENTARIO_RECHAZO)
                self.assertEqual(rechazo.status_code, 403)
        self.assertEqual(self.estado_actual(solicitud_id), "Pendiente")

    def test_no_se_puede_suplantar_el_rol_desde_la_peticion(self):
        solicitud_id = self.crear_pendiente_direccion()

        response = self.aprobar(solicitud_id, rol_autorizador="Dirección", autorizador_nombre="Carlos Ruiz")

        self.assertEqual(response.status_code, 403)

    def test_autorizador_inexistente_devuelve_422(self):
        solicitud_id = self.crear_pendiente()

        response = self.aprobar(solicitud_id, autorizador_id="NADIE")

        self.assertEqual(response.status_code, 422)
        self.assertIn("NADIE", response.json()["detail"])

    def test_solicitud_inexistente_o_eliminada_devuelve_404(self):
        eliminada = self.crear_pendiente()
        self.client.delete(f"/api/solicitudes/{eliminada}")

        for solicitud_id in (uuid4(), eliminada):
            with self.subTest(solicitud_id=solicitud_id):
                self.assertEqual(self.aprobar(solicitud_id).status_code, 404)
                self.assertEqual(self.rechazar(solicitud_id, comentario=COMENTARIO_RECHAZO).status_code, 404)

    def test_decision_documenta_respuestas_de_error(self):
        paths = self.client.get("/openapi.json").json()["paths"]

        for accion in ("aprobar", "rechazar"):
            operacion = paths[f"/api/solicitudes/{{solicitud_id}}/{accion}"]["post"]
            with self.subTest(accion=accion):
                for codigo in ("403", "404", "409", "422"):
                    self.assertIn(codigo, operacion["responses"])


class TestHU05Servicio(unittest.TestCase):
    def setUp(self):
        self.service = SolicitudFondoService()
        self.solicitud = self.service.crear_solicitud(
            SolicitudFondoCreate(
                obra_id="OBRA-NORTE-01",
                solicitante_id="RESIDENTE-PAU",
                etapa_construccion="cimentación",
                partida_categoria="Renta de Maquinaria",
                concepto="Renta de retroexcavadora para sondeo",
                monto_solicitado=Decimal("3500.00"),
                costo_estimado=Decimal("4000.00"),
                urgencia="urgente",
                evidencia_url="https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
            )
        ).solicitud

    def test_aprobar_actualiza_estado_y_registra_autorizacion(self):
        resultado = self.service.aprobar_solicitud(self.solicitud.id, AprobacionCreate(**ADMINISTRACION))

        self.assertEqual(resultado.estado, EstadoSolicitud.APROBADO)
        self.assertEqual(resultado.autorizacion.monto_autorizado, Decimal("3500.00"))
        self.assertEqual(resultado.updated_at, resultado.autorizacion.fecha_decision)

    def test_rechazar_actualiza_estado_y_registra_comentario(self):
        resultado = self.service.rechazar_solicitud(
            self.solicitud.id,
            RechazoCreate(**ADMINISTRACION, comentario=COMENTARIO_RECHAZO),
        )

        self.assertEqual(resultado.estado, EstadoSolicitud.RECHAZADO)
        self.assertEqual(resultado.autorizacion.comentario, COMENTARIO_RECHAZO)

    def test_rechazo_sin_comentario_no_se_puede_construir(self):
        with self.assertRaises(ValueError):
            RechazoCreate(**ADMINISTRACION)

    def test_errores_de_negocio(self):
        with self.assertRaises(SolicitudNoEncontradaError):
            self.service.aprobar_solicitud(uuid4(), AprobacionCreate(**ADMINISTRACION))

        self.service.aprobar_solicitud(self.solicitud.id, AprobacionCreate(**ADMINISTRACION))
        with self.assertRaises(SolicitudNoPendienteError):
            self.service.aprobar_solicitud(self.solicitud.id, AprobacionCreate(**DIRECCION))

    def test_administracion_no_puede_decidir_nivel_direccion(self):
        alta = self.service.crear_solicitud(
            SolicitudFondoCreate(
                **{
                    **self.solicitud.model_dump(include=set(SolicitudFondoCreate.model_fields)),
                    "monto_solicitado": Decimal("18000.00"),
                    "firma_digital_direccion": "FIRMA-DIR-001",
                }
            )
        ).solicitud

        with self.assertRaises(AutorizadorNoPermitidoError):
            self.service.aprobar_solicitud(alta.id, AprobacionCreate(**ADMINISTRACION))


if __name__ == "__main__":
    unittest.main()
