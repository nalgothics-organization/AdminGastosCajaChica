"""Tests del flujo del prototipo de la Iteración 4: gasto sin solicitud previa (RF07/HU07),
saldos por obra (RF10/HU10) y persistencia en base de datos.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal
from uuid import UUID

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.comprobante_service import ComprobanteService, comprobante_service
from src.services.solicitud_service import SolicitudFondoService, solicitud_service
from tests.test_hu07_comprobacion import BaseHU07TestCase
from tests.test_hu16_captura_rapida import crear_solicitud_aprobada

DATOS_SIN_SOLICITUD = {
    "tipo": "ticket",
    "monto_comprobado": "850.00",
    "fecha_gasto": date.today().isoformat(),
    "proveedor": "Ferretería La Obra",
    "concepto": "Cemento y varilla urgentes",
    "obra_id": "OBRA-SUR-02",
    "etapa_construccion": "estructura",
    "partida_categoria": "Materiales",
}


class TestGastoSinSolicitud(BaseHU07TestCase):
    def test_foto_sin_solicitud_se_comprueba_indicando_obra_etapa_y_partida(self):
        comprobante_id = self.capturar().json()["id"]

        response = self.client.put(f"/api/comprobantes/{comprobante_id}/datos", json=DATOS_SIN_SOLICITUD)

        self.assertEqual(response.status_code, 200)
        cuerpo = response.json()
        self.assertIsNone(cuerpo["solicitud_id"])
        self.assertEqual(cuerpo["obra_id"], "OBRA-SUR-02")
        self.assertEqual(cuerpo["partida_categoria"], "Materiales")

    def test_sin_solicitud_ni_clasificacion_se_rechaza(self):
        comprobante_id = self.capturar().json()["id"]
        datos = {k: v for k, v in DATOS_SIN_SOLICITUD.items() if k != "obra_id"}

        response = self.client.put(f"/api/comprobantes/{comprobante_id}/datos", json=datos)

        self.assertEqual(response.status_code, 422)
        self.assertIn("Seleccione la solicitud", response.json()["detail"])

    def test_gasto_sin_solicitud_siempre_queda_en_revision_aunque_tenga_factura(self):
        comprobante_id = self.capturar().json()["id"]
        self.client.put(
            f"/api/comprobantes/{comprobante_id}/datos", json={**DATOS_SIN_SOLICITUD, "tipo": "factura"}
        )

        cerrado = self.cerrar(comprobante_id)

        self.assertEqual(cerrado.status_code, 200)
        self.assertEqual(cerrado.json()["estado"], "Revisión contabilidad")

    def test_partida_de_maquinaria_sin_solicitud_exige_horas(self):
        comprobante_id = self.capturar().json()["id"]
        datos = {**DATOS_SIN_SOLICITUD, "partida_categoria": "Renta de Maquinaria"}

        response = self.client.put(f"/api/comprobantes/{comprobante_id}/datos", json=datos)

        self.assertEqual(response.status_code, 422)
        self.assertIn("horas", response.json()["detail"].lower())


class TestSaldosPorObra(BaseHU07TestCase):
    def saldo(self, obra_id):
        saldos = self.client.get("/api/saldos").json()
        return next(s for s in saldos if s["obra_id"] == obra_id)

    def test_sin_movimientos_cada_obra_muestra_su_fondo_completo(self):
        saldos = self.client.get("/api/saldos").json()

        self.assertEqual({s["obra_id"] for s in saldos}, {"OBRA-NORTE-01", "OBRA-SUR-02", "OBRA-PONIENTE-03"})
        for saldo in saldos:
            self.assertEqual(Decimal(saldo["disponible_caja_chica"]), Decimal(saldo["presupuesto_caja_chica"]))
            self.assertEqual(Decimal(saldo["autorizado"]), Decimal("0"))

    def test_solicitud_pendiente_cuenta_como_pendiente_de_autorizacion(self):
        self.client.post("/api/solicitudes", json={
            "obra_id": "OBRA-NORTE-01", "solicitante_id": "RESIDENTE-PAU",
            "etapa_construccion": "cimentación", "partida_categoria": "Materiales",
            "concepto": "Compra de grava", "monto_solicitado": "1200.00", "costo_estimado": "1300.00",
            "urgencia": "media", "evidencia_url": "https://storage.empresa.com/evidencias/grava.jpg",
        })

        saldo = self.saldo("OBRA-NORTE-01")

        self.assertEqual(Decimal(saldo["pendiente_autorizacion"]), Decimal("1200.00"))
        self.assertEqual(saldo["solicitudes_pendientes"], 1)
        self.assertEqual(Decimal(saldo["autorizado"]), Decimal("0"))

    def test_saldo_descuenta_lo_comprobado_de_lo_autorizado(self):
        comprobante_id = self.capturar_vinculado()
        self.completar(comprobante_id)
        self.cerrar(comprobante_id)

        saldo = self.saldo("OBRA-NORTE-01")

        self.assertEqual(Decimal(saldo["autorizado"]), Decimal("3500.00"))
        self.assertEqual(Decimal(saldo["comprobado"]), Decimal("3200.00"))
        self.assertEqual(Decimal(saldo["por_comprobar"]), Decimal("300.00"))
        self.assertEqual(Decimal(saldo["disponible_caja_chica"]), Decimal("16500.00"))
        self.assertEqual(Decimal(saldo["porcentaje_autorizado"]), Decimal("17.5"))
        self.assertEqual(Decimal(saldo["porcentaje_gastado"]), Decimal("91.4"))
        self.assertEqual(saldo["comprobantes_en_revision"], 1)

    def test_borrador_no_descuenta_del_saldo(self):
        comprobante_id = self.capturar_vinculado()
        self.completar(comprobante_id)

        saldo = self.saldo("OBRA-NORTE-01")

        self.assertEqual(Decimal(saldo["comprobado"]), Decimal("0"))
        self.assertEqual(Decimal(saldo["por_comprobar"]), Decimal("3500.00"))

    def test_reverso_devuelve_el_saldo_y_ajuste_lo_sustituye(self):
        comprobante_id = self.capturar_vinculado()
        self.completar(comprobante_id)
        self.cerrar(comprobante_id)

        self.client.post(f"/api/comprobantes/{comprobante_id}/ajustes", json={
            "tipo_registro": "reverso", "motivo": "Se capturó el comprobante equivocado",
        })
        self.assertEqual(Decimal(self.saldo("OBRA-NORTE-01")["comprobado"]), Decimal("0"))

    def test_ajuste_cambia_el_monto_comprobado(self):
        comprobante_id = self.capturar_vinculado()
        self.completar(comprobante_id)
        self.cerrar(comprobante_id)
        datos = {
            "tipo": "nota_simple", "monto_comprobado": "3000.00", "fecha_gasto": date.today().isoformat(),
            "proveedor": "Maquinaria El Güero", "concepto": "Renta de retroexcavadora",
            "horas": "4.0", "unidad_horas": "maquinaria",
        }

        self.client.post(f"/api/comprobantes/{comprobante_id}/ajustes", json={
            "tipo_registro": "ajuste", "motivo": "El monto correcto es menor", "datos": datos,
        })

        self.assertEqual(Decimal(self.saldo("OBRA-NORTE-01")["comprobado"]), Decimal("3000.00"))

    def test_gasto_sin_solicitud_es_reembolso_pendiente_y_no_baja_el_saldo(self):
        comprobante_id = self.capturar().json()["id"]
        self.client.put(f"/api/comprobantes/{comprobante_id}/datos", json=DATOS_SIN_SOLICITUD)
        self.cerrar(comprobante_id)

        saldo = self.saldo("OBRA-SUR-02")

        self.assertEqual(Decimal(saldo["gasto_sin_solicitud"]), Decimal("850.00"))
        self.assertEqual(Decimal(saldo["comprobado"]), Decimal("0"))


class TestPersistencia(BaseHU07TestCase):
    def test_los_datos_sobreviven_a_una_instancia_nueva_del_servicio(self):
        solicitud = crear_solicitud_aprobada()
        comprobante_id = self.capturar().json()["id"]
        self.completar(comprobante_id, solicitud_id=str(solicitud.id))
        self.cerrar(comprobante_id)

        solicitudes = SolicitudFondoService()
        comprobantes = ComprobanteService(solicitudes=solicitudes, uploads_dir=self._tmp.name)

        recuperada = solicitudes.obtener_por_id(solicitud.id)
        self.assertEqual(recuperada.estado.value, "Aprobado")
        self.assertEqual(recuperada.autorizacion.autorizador_nombre, "Laura Méndez")
        self.assertEqual(recuperada.monto_solicitado, Decimal("3500.00"))
        recuperado = comprobantes.obtener_por_id(UUID(comprobante_id))
        self.assertEqual(recuperado.estado.value, "Revisión contabilidad")
        self.assertEqual(recuperado.datos.monto_comprobado, Decimal("3200.00"))

    def test_el_folio_no_se_repite_aunque_se_reinicie_el_servicio(self):
        crear_solicitud_aprobada()
        crear_solicitud_aprobada()

        folios = [s.folio for s in SolicitudFondoService().listar_solicitudes_activas()]

        self.assertEqual(len(folios), len(set(folios)))
        self.assertTrue(folios[-1].endswith("1002"))

    def test_singletons_comparten_la_misma_base(self):
        solicitud = crear_solicitud_aprobada()

        self.assertIsNotNone(solicitud_service.obtener_por_id(solicitud.id))
        self.assertEqual(comprobante_service.listar(), [])


if __name__ == "__main__":
    unittest.main()
