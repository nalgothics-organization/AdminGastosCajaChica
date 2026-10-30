"""Tests de RF07/HU07: formulario de comprobación con horas condicionales,
inmutabilidad tras el cierre y correcciones por Ajuste/Reverso (AGENTS.md §8).
"""

import os
import sys
import unittest
from datetime import date, timedelta
from uuid import UUID

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.comprobante_service import comprobante_service
from tests.test_hu16_captura_rapida import BaseComprobanteTestCase, crear_solicitud_aprobada

DATOS_MAQUINARIA = {
    "tipo": "nota_simple",
    "monto_comprobado": "3200.00",
    "fecha_gasto": date.today().isoformat(),
    "proveedor": "Maquinaria El Güero",
    "concepto": "Renta de retroexcavadora",
    "horas": "4.5",
    "unidad_horas": "maquinaria",
}


class BaseHU07TestCase(BaseComprobanteTestCase):
    def capturar_vinculado(self, partida="Renta de Maquinaria"):
        """Crea una solicitud aprobada y captura una foto; `completar` la vincula a esa solicitud."""
        self.solicitud = crear_solicitud_aprobada(partida=partida)
        return self.capturar().json()["id"]

    def completar(self, comprobante_id, **cambios):
        datos = {**DATOS_MAQUINARIA, **cambios}
        # El residente elige la solicitud al comprobar; por defecto la que creó capturar_vinculado
        solicitud = getattr(self, "solicitud", None)
        if solicitud and "solicitud_id" not in datos:
            datos["solicitud_id"] = str(solicitud.id)
        return self.client.put(f"/api/comprobantes/{comprobante_id}/datos", json=datos)

    def cerrar(self, comprobante_id):
        return self.client.post(f"/api/comprobantes/{comprobante_id}/cerrar")


class TestHU07DatosComprobacion(BaseHU07TestCase):
    def test_criterio_3_nota_simple_con_concepto_horas_proveedor_y_monto(self):
        comprobante_id = self.capturar_vinculado()

        response = self.completar(comprobante_id)

        self.assertEqual(response.status_code, 200)
        datos = response.json()["datos"]
        self.assertEqual(datos["horas"], "4.5")
        self.assertEqual(datos["unidad_horas"], "maquinaria")
        self.assertEqual(datos["proveedor"], "Maquinaria El Güero")
        self.assertEqual(datos["solicitud_id"], str(self.solicitud.id))

    def test_partida_de_maquinaria_exige_horas(self):
        comprobante_id = self.capturar_vinculado()

        response = self.completar(comprobante_id, horas=None, unidad_horas=None)

        self.assertEqual(response.status_code, 422)
        self.assertIn("horas", response.json()["detail"])

    def test_mano_de_obra_exige_horas_de_trabajo(self):
        comprobante_id = self.capturar_vinculado(partida="Mano de Obra")

        response = self.completar(comprobante_id, unidad_horas="trabajo")

        self.assertEqual(response.status_code, 200)

    def test_partida_sin_horas_rechaza_que_se_envien(self):
        comprobante_id = self.capturar_vinculado(partida="Materiales")

        con_horas = self.completar(comprobante_id)
        sin_horas = self.completar(comprobante_id, horas=None, unidad_horas=None)

        self.assertEqual(con_horas.status_code, 422)
        self.assertEqual(sin_horas.status_code, 200)

    def test_horas_sin_unidad_es_invalido(self):
        comprobante_id = self.capturar_vinculado()

        response = self.completar(comprobante_id, unidad_horas=None)

        self.assertEqual(response.status_code, 422)

    def test_campos_obligatorios_y_monto_positivo(self):
        comprobante_id = self.capturar_vinculado()

        for cambio in ({"proveedor": ""}, {"concepto": ""}, {"monto_comprobado": "0"}, {"tipo": "vale"}):
            with self.subTest(cambio=cambio):
                self.assertEqual(self.completar(comprobante_id, **cambio).status_code, 422)

    def test_fecha_futura_es_invalida(self):
        comprobante_id = self.capturar_vinculado()
        manana = (date.today() + timedelta(days=1)).isoformat()

        response = self.completar(comprobante_id, fecha_gasto=manana)

        self.assertEqual(response.status_code, 422)

    def test_foto_sin_solicitud_se_vincula_al_completar(self):
        comprobante_id = self.capturar().json()["id"]
        solicitud = crear_solicitud_aprobada()

        sin_solicitud = self.completar(comprobante_id)
        con_solicitud = self.completar(comprobante_id, solicitud_id=str(solicitud.id))

        self.assertEqual(sin_solicitud.status_code, 422)
        self.assertEqual(con_solicitud.status_code, 200)
        self.assertEqual(con_solicitud.json()["solicitud_id"], str(solicitud.id))
        self.assertTrue(con_solicitud.json()["requiere_horas"])

    def test_no_se_vincula_solicitud_de_otro_residente(self):
        comprobante_id = self.capturar().json()["id"]
        ajena = crear_solicitud_aprobada(solicitante="OTRO-RESIDENTE")

        response = self.completar(comprobante_id, solicitud_id=str(ajena.id))

        self.assertEqual(response.status_code, 422)


class TestHU07CierreEInmutabilidad(BaseHU07TestCase):
    def test_no_se_cierra_sin_datos(self):
        comprobante_id = self.capturar_vinculado()

        self.assertEqual(self.cerrar(comprobante_id).status_code, 422)

    def test_factura_queda_comprobada_y_nota_en_revision(self):
        factura_id = self.capturar_vinculado()
        self.completar(factura_id, tipo="factura")
        nota_id = self.capturar().json()["id"]
        self.completar(nota_id)

        self.assertEqual(self.cerrar(factura_id).json()["estado"], "Comprobado")
        self.assertEqual(self.cerrar(nota_id).json()["estado"], "Revisión contabilidad")

    def test_comprobante_cerrado_no_se_modifica_ni_elimina(self):
        comprobante_id = self.capturar_vinculado()
        self.completar(comprobante_id, tipo="factura")
        self.cerrar(comprobante_id)

        actualizar = self.completar(comprobante_id, monto_comprobado="1.00")
        eliminar = self.client.delete(f"/api/comprobantes/{comprobante_id}")
        recerrar = self.cerrar(comprobante_id)

        self.assertEqual(actualizar.status_code, 409)
        self.assertEqual(eliminar.status_code, 409)
        self.assertEqual(recerrar.status_code, 409)
        original = self.client.get(f"/api/comprobantes/{comprobante_id}").json()
        self.assertEqual(original["datos"]["monto_comprobado"], "3200.00")

    def test_borrador_se_descarta_con_soft_delete(self):
        comprobante_id = self.capturar_vinculado()

        eliminar = self.client.delete(f"/api/comprobantes/{comprobante_id}")

        self.assertEqual(eliminar.status_code, 204)
        self.assertEqual(self.client.get(f"/api/comprobantes/{comprobante_id}").status_code, 404)
        registro = comprobante_service._db[UUID(comprobante_id)]
        self.assertFalse(registro.activo)
        self.assertIsNotNone(registro.deleted_at)


class TestHU07AjustesYReversos(BaseHU07TestCase):
    def setUp(self):
        super().setUp()
        self.original_id = self.capturar_vinculado()
        self.completar(self.original_id, tipo="factura")
        self.cerrar(self.original_id)

    def corregir(self, **cuerpo):
        return self.client.post(f"/api/comprobantes/{self.original_id}/ajustes", json=cuerpo)

    def test_ajuste_crea_registro_nuevo_que_referencia_al_original(self):
        datos = {**DATOS_MAQUINARIA, "tipo": "factura", "monto_comprobado": "3000.00"}

        response = self.corregir(tipo_registro="ajuste", motivo="Monto mal capturado", datos=datos)

        self.assertEqual(response.status_code, 201)
        ajuste = response.json()
        self.assertNotEqual(ajuste["id"], self.original_id)
        self.assertEqual(ajuste["comprobante_origen_id"], self.original_id)
        self.assertEqual(ajuste["tipo_registro"], "ajuste")
        self.assertEqual(ajuste["estado"], "Revisión contabilidad")
        original = self.client.get(f"/api/comprobantes/{self.original_id}").json()
        self.assertEqual(original["datos"]["monto_comprobado"], "3200.00")

    def test_ajuste_respeta_la_regla_de_horas(self):
        datos = {**DATOS_MAQUINARIA, "horas": None, "unidad_horas": None}

        response = self.corregir(tipo_registro="ajuste", motivo="Sin horas", datos=datos)

        self.assertEqual(response.status_code, 422)

    def test_reverso_no_lleva_datos_y_solo_se_permite_una_vez(self):
        primero = self.corregir(tipo_registro="reverso", motivo="Comprobante duplicado")
        segundo = self.corregir(tipo_registro="reverso", motivo="Comprobante duplicado")
        con_datos = self.corregir(tipo_registro="reverso", motivo="Con datos", datos=DATOS_MAQUINARIA)

        self.assertEqual(primero.status_code, 201)
        self.assertEqual(primero.json()["datos"]["monto_comprobado"], "3200.00")
        self.assertEqual(segundo.status_code, 409)
        self.assertEqual(con_datos.status_code, 422)

    def test_borrador_no_admite_ajuste(self):
        borrador_id = self.capturar().json()["id"]

        response = self.client.post(
            f"/api/comprobantes/{borrador_id}/ajustes",
            json={"tipo_registro": "reverso", "motivo": "No aplica"},
        )

        self.assertEqual(response.status_code, 409)


if __name__ == "__main__":
    unittest.main()
