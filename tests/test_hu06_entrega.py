"""Tests de RF06/HU06: registro de la entrega física o digital del recurso.
La administración registra forma de entrega, fecha, referencia y quién entregó el dinero de una
solicitud aprobada, y el registro queda visible al consultar la solicitud.
"""

import os
import sys
import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from uuid import UUID, uuid4

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.models.solicitud import EntregaCreate
from src.services.solicitud_service import (
    LIMITE_DIAS_COMPROBACION_DEFAULT,
    EntregaNoPermitidaError,
    SolicitudBloqueadaError,
    solicitud_service,
)
from tests.test_hu04_bloqueo import ADMINISTRACION, OTRO_RESIDENTE, PAYLOAD_SOLICITUD, BaseBloqueoTestCase
from tests.test_hu05_autorizacion import DIRECCION
from tests.test_hu16_captura_rapida import RESIDENTE, crear_solicitud_aprobada

QUIEN_ENTREGA = {
    "entregado_por_id": "ADM-LAURA",
    "entregado_por_nombre": "Laura Méndez",
    "rol_entrega": "Administración",
}
TRANSFERENCIA = {**QUIEN_ENTREGA, "forma_entrega": "Transferencia", "referencia": "SPEI-20261127-0381"}
EFECTIVO = {**QUIEN_ENTREGA, "forma_entrega": "Efectivo"}


class BaseEntregaTestCase(BaseBloqueoTestCase):
    def entregar(self, solicitud_id, **cuerpo):
        return self.client.post(f"/api/solicitudes/{solicitud_id}/entrega", json={**TRANSFERENCIA, **cuerpo})

    def solicitud_aprobada_id(self, solicitante=RESIDENTE):
        return str(crear_solicitud_aprobada(solicitante=solicitante).id)

    def consultar(self, solicitud_id):
        return self.client.get(f"/api/solicitudes/{solicitud_id}").json()


class TestHU06RegistroDeEntrega(BaseEntregaTestCase):
    def test_criterio_1_transferencia_se_registra_con_su_referencia_bancaria(self):
        """Dado que una solicitud está autorizada, cuando entrego el recurso,
        entonces el sistema me permite añadir la referencia bancaria."""
        solicitud_id = self.solicitud_aprobada_id()

        response = self.entregar(solicitud_id)

        self.assertEqual(response.status_code, 201)
        entrega = response.json()["entrega"]
        self.assertEqual(entrega["forma_entrega"], "Transferencia")
        self.assertEqual(entrega["referencia"], "SPEI-20261127-0381")
        self.assertTrue(entrega["fecha_registro"])

    def test_criterio_1_efectivo_se_marca_sin_referencia(self):
        """... o marcar efectivo."""
        solicitud_id = self.solicitud_aprobada_id()

        response = self.client.post(f"/api/solicitudes/{solicitud_id}/entrega", json=EFECTIVO)

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["entrega"]["forma_entrega"], "Efectivo")
        self.assertIsNone(response.json()["entrega"]["referencia"])

    def test_efectivo_puede_llevar_un_folio_opcional(self):
        solicitud_id = self.solicitud_aprobada_id()

        response = self.client.post(
            f"/api/solicitudes/{solicitud_id}/entrega", json={**EFECTIVO, "referencia": "  Recibo 118  "}
        )

        self.assertEqual(response.json()["entrega"]["referencia"], "Recibo 118")

    def test_tarjeta_tambien_exige_referencia(self):
        solicitud_id = self.solicitud_aprobada_id()

        ok = self.entregar(solicitud_id, forma_entrega="Tarjeta", referencia="TC-4412-0098")

        self.assertEqual(ok.status_code, 201)
        self.assertEqual(ok.json()["entrega"]["forma_entrega"], "Tarjeta")

    def test_transferencia_o_tarjeta_sin_referencia_devuelven_422(self):
        for forma in ("Transferencia", "Tarjeta"):
            for referencia in (None, "", "   ", "ab"):
                with self.subTest(forma=forma, referencia=referencia):
                    solicitud_id = self.solicitud_aprobada_id()

                    response = self.entregar(solicitud_id, forma_entrega=forma, referencia=referencia)

                    self.assertEqual(response.status_code, 422)
                    self.assertIn("referencia bancaria", response.text)
                    self.assertIsNone(self.consultar(solicitud_id)["entrega"])

    def test_forma_de_entrega_desconocida_devuelve_422(self):
        solicitud_id = self.solicitud_aprobada_id()

        self.assertEqual(self.entregar(solicitud_id, forma_entrega="Cheque").status_code, 422)

    def test_nombre_de_quien_entrega_es_obligatorio(self):
        solicitud_id = self.solicitud_aprobada_id()

        for campo in ("entregado_por_id", "entregado_por_nombre"):
            with self.subTest(campo=campo):
                self.assertEqual(self.entregar(solicitud_id, **{campo: "  "}).status_code, 422)

    def test_criterio_2_al_consultar_la_solicitud_aparece_quien_dispersó_el_recurso(self):
        """Dado que se guarda el registro de entrega, cuando se consulta la solicitud,
        entonces aparece el nombre de la persona que dispersó el recurso."""
        solicitud_id = self.solicitud_aprobada_id()
        self.entregar(solicitud_id)

        consultada = self.consultar(solicitud_id)
        en_lista = next(s for s in self.client.get("/api/solicitudes").json() if s["id"] == solicitud_id)

        for solicitud in (consultada, en_lista):
            self.assertEqual(solicitud["entrega"]["entregado_por_nombre"], "Laura Méndez")
            self.assertEqual(solicitud["entrega"]["entregado_por_id"], "ADM-LAURA")
            self.assertEqual(solicitud["entrega"]["rol_entrega"], "Administración")

    def test_criterio_3_solicitud_recien_aprobada_queda_lista_para_entregar(self):
        """Dado que acabo de aprobar una solicitud, cuando reviso el apartado de entregas,
        entonces aparece lista para registrar su entrega: aprobada y sin entrega."""
        pendiente = self.pedir_fondo().json()["solicitud"]
        self.assertEqual(self.aprobar(pendiente["id"]).status_code, 200)

        por_entregar = [
            s for s in self.client.get("/api/solicitudes").json() if s["estado"] == "Aprobado" and not s["entrega"]
        ]

        self.assertEqual([s["id"] for s in por_entregar], [pendiente["id"]])
        self.assertEqual(self.entregar(pendiente["id"]).status_code, 201)
        por_entregar = [
            s for s in self.client.get("/api/solicitudes").json() if s["estado"] == "Aprobado" and not s["entrega"]
        ]
        self.assertEqual(por_entregar, [])

    def test_el_registro_persiste_y_la_solicitud_sigue_aprobada(self):
        solicitud_id = self.solicitud_aprobada_id()
        self.entregar(solicitud_id)

        guardada = solicitud_service.obtener_por_id(UUID(solicitud_id))

        self.assertEqual(guardada.estado.value, "Aprobado")
        self.assertEqual(guardada.entrega.entregado_por_nombre, "Laura Méndez")
        self.assertEqual(guardada.autorizacion.autorizador_nombre, "Laura Méndez")

    def test_direccion_tambien_puede_registrar_la_entrega(self):
        solicitud_id = self.solicitud_aprobada_id()

        response = self.entregar(
            solicitud_id,
            entregado_por_id=DIRECCION["autorizador_id"],
            entregado_por_nombre=DIRECCION["autorizador_nombre"],
            rol_entrega="Dirección",
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["entrega"]["rol_entrega"], "Dirección")

    def test_una_solicitud_de_direccion_la_puede_entregar_administracion(self):
        alta = self.client.post(
            "/api/solicitudes",
            json={**PAYLOAD_SOLICITUD, "monto_solicitado": "18000.00", "firma_digital_direccion": "FIRMA-DIR-001"},
        )
        alta_id = alta.json()["solicitud"]["id"]
        self.assertEqual(self.client.post(f"/api/solicitudes/{alta_id}/aprobar", json=DIRECCION).status_code, 200)

        response = self.entregar(alta_id)  # entrega registrada por Administración

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json()["entrega"]["rol_entrega"], "Administración")


class TestHU06EstadoDeLaSolicitud(BaseEntregaTestCase):
    def test_solicitud_pendiente_no_se_entrega(self):
        pendiente = self.pedir_fondo().json()["solicitud"]

        response = self.entregar(pendiente["id"])

        self.assertEqual(response.status_code, 409)
        self.assertIn("aprobada", response.json()["detail"])
        self.assertIsNone(self.consultar(pendiente["id"])["entrega"])

    def test_solicitud_rechazada_no_se_entrega(self):
        pendiente = self.pedir_fondo().json()["solicitud"]
        self.client.post(
            f"/api/solicitudes/{pendiente['id']}/rechazar",
            json={**ADMINISTRACION, "comentario": "El gasto no corresponde a la etapa."},
        )

        response = self.entregar(pendiente["id"])

        self.assertEqual(response.status_code, 409)
        self.assertIn("Rechazado", response.json()["detail"])

    def test_la_entrega_se_registra_una_sola_vez_y_no_se_modifica(self):
        solicitud_id = self.solicitud_aprobada_id()
        self.entregar(solicitud_id)

        segunda = self.entregar(solicitud_id, forma_entrega="Tarjeta", referencia="TC-0001")

        self.assertEqual(segunda.status_code, 409)
        self.assertIn("ya tiene su entrega", segunda.json()["detail"])
        original = self.consultar(solicitud_id)["entrega"]
        self.assertEqual(original["forma_entrega"], "Transferencia")
        self.assertEqual(original["referencia"], "SPEI-20261127-0381")

    def test_solicitud_inexistente_devuelve_404(self):
        self.assertEqual(self.entregar(uuid4()).status_code, 404)

    def test_solicitud_eliminada_logicamente_devuelve_404(self):
        solicitud_id = self.solicitud_aprobada_id()
        self.client.delete(f"/api/solicitudes/{solicitud_id}")

        self.assertEqual(self.entregar(solicitud_id).status_code, 404)

    def test_el_servicio_levanta_el_error_de_negocio(self):
        pendiente = self.pedir_fondo().json()["solicitud"]

        with self.assertRaises(EntregaNoPermitidaError):
            solicitud_service.registrar_entrega(UUID(pendiente["id"]), EntregaCreate(**TRANSFERENCIA))


class TestHU06FechaDeEntrega(BaseEntregaTestCase):
    def test_sin_fecha_se_toma_el_dia_de_hoy(self):
        solicitud_id = self.solicitud_aprobada_id()

        entrega = self.entregar(solicitud_id).json()["entrega"]

        self.assertEqual(entrega["fecha_entrega"], datetime.now(timezone.utc).date().isoformat())

    def test_se_guarda_la_fecha_indicada(self):
        solicitud_id = self.solicitud_aprobada_id()
        hoy = datetime.now(timezone.utc).date()

        entrega = self.entregar(solicitud_id, fecha_entrega=hoy.isoformat()).json()["entrega"]

        self.assertEqual(entrega["fecha_entrega"], hoy.isoformat())

    def test_fecha_futura_devuelve_422(self):
        solicitud_id = self.solicitud_aprobada_id()
        manana = datetime.now(timezone.utc).date() + timedelta(days=1)

        response = self.entregar(solicitud_id, fecha_entrega=manana.isoformat())

        self.assertEqual(response.status_code, 422)
        self.assertIn("futura", response.json()["detail"])

    def test_fecha_anterior_a_la_autorizacion_devuelve_422(self):
        solicitud_id = self.solicitud_aprobada_id()
        antes = datetime.now(timezone.utc).date() - timedelta(days=3)

        response = self.entregar(solicitud_id, fecha_entrega=antes.isoformat())

        self.assertEqual(response.status_code, 422)
        self.assertIn("anterior a la autorización", response.json()["detail"])

    def test_el_dia_anterior_se_acepta_por_la_diferencia_de_zona_horaria(self):
        solicitud_id = self.solicitud_aprobada_id()
        ayer = datetime.now(timezone.utc).date() - timedelta(days=1)

        self.assertEqual(self.entregar(solicitud_id, fecha_entrega=ayer.isoformat()).status_code, 201)

    def test_fecha_con_formato_invalido_devuelve_422(self):
        solicitud_id = self.solicitud_aprobada_id()

        self.assertEqual(self.entregar(solicitud_id, fecha_entrega="27/11/2026").status_code, 422)

    def test_la_fecha_de_hoy_sigue_el_reloj_del_servicio(self):
        solicitud_id = self.solicitud_aprobada_id()
        self.avanzar_dias(2)

        entrega = self.entregar(solicitud_id).json()["entrega"]

        self.assertEqual(date.fromisoformat(entrega["fecha_entrega"]), solicitud_service.reloj().date())


class TestHU06BloqueoPorComprobacionesVencidas(BaseEntregaTestCase):
    """RF04: tampoco se entrega un fondo nuevo a quien tiene comprobaciones vencidas."""

    def test_no_se_entrega_fondo_nuevo_con_un_fondo_entregado_sin_comprobar_vencido(self):
        vencida = crear_solicitud_aprobada()
        nueva = crear_solicitud_aprobada()
        self.assertEqual(self.entregar(str(vencida.id)).status_code, 201)
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        response = self.entregar(str(nueva.id))

        self.assertEqual(response.status_code, 423)
        self.assertIn(vencida.folio, response.json()["detail"])
        self.assertIsNone(self.consultar(str(nueva.id))["entrega"])

    def test_el_servicio_tambien_impide_entregar(self):
        vencida = crear_solicitud_aprobada()
        nueva = crear_solicitud_aprobada()
        solicitud_service.registrar_entrega(vencida.id, EntregaCreate(**TRANSFERENCIA))
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        with self.assertRaises(SolicitudBloqueadaError):
            solicitud_service.registrar_entrega(nueva.id, EntregaCreate(**TRANSFERENCIA))

    def test_al_comprobar_el_fondo_vencido_se_desbloquea_la_entrega(self):
        self.solicitud = crear_solicitud_aprobada()
        nueva = crear_solicitud_aprobada()
        self.assertEqual(self.entregar(str(self.solicitud.id)).status_code, 201)
        self.comprobar("3500.00")
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.entregar(str(nueva.id)).status_code, 201)

    def test_un_fondo_que_nunca_se_entrego_no_bloquea_otras_entregas(self):
        """El dinero que no ha salido no se debe comprobar: dos fondos viejos sin entregar no se bloquean entre sí."""
        sin_entregar = crear_solicitud_aprobada()
        nueva = crear_solicitud_aprobada()
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.entregar(str(nueva.id)).status_code, 201)
        self.assertIsNone(self.consultar(str(sin_entregar.id))["entrega"])

    def test_una_solicitud_no_se_bloquea_a_si_misma(self):
        sola = crear_solicitud_aprobada()
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.entregar(str(sola.id)).status_code, 201)

    def test_el_bloqueo_es_por_residente(self):
        vencida = crear_solicitud_aprobada()
        ajena = crear_solicitud_aprobada(solicitante=OTRO_RESIDENTE)
        self.entregar(str(vencida.id))
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertEqual(self.entregar(str(ajena.id)).status_code, 201)

    def test_bloqueo_de_sin_filtros_conserva_su_comportamiento_original(self):
        """La bandeja de autorización sigue contando fondos aprobados aunque no se hayan entregado (RF04)."""
        crear_solicitud_aprobada()
        self.avanzar_dias(LIMITE_DIAS_COMPROBACION_DEFAULT + 1)

        self.assertTrue(solicitud_service.bloqueo_de(RESIDENTE).bloqueada)
        self.assertFalse(solicitud_service.bloqueo_de(RESIDENTE, solo_entregadas=True).bloqueada)
        self.assertEqual(
            solicitud_service.bloqueo_de(RESIDENTE).monto_por_comprobar, Decimal("3500.00")
        )


if __name__ == "__main__":
    unittest.main()
