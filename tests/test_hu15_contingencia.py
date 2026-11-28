"""Tests de RF14/HU15: distinción entre gasto cobrable al cliente y fondo de contingencia.
Administración clasifica el gasto al aprobar la solicitud y el saldo del fondo de contingencia
de la obra se actualiza cuando se comprueba un gasto cargado a él.
"""

import os
import sys
import unittest
from datetime import date
from decimal import Decimal

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from sqlalchemy import create_engine, inspect, text
from sqlalchemy.pool import StaticPool

from src.database import agregar_columnas_faltantes
from src.services.obra_catalogo import OBRAS
from tests.test_hu07_comprobacion import BaseHU07TestCase
from tests.test_hu16_captura_rapida import crear_solicitud_aprobada

OBRA = "OBRA-NORTE-01"
FONDO_CONTINGENCIA = next(o.fondo_contingencia for o in OBRAS if o.id == OBRA)
ADMINISTRACION = {
    "autorizador_id": "ADMIN-LAURA",
}
SOLICITUD = {
    "obra_id": OBRA,
    "solicitante_id": "RESIDENTE-PAU",
    "etapa_construccion": "acabados",
    "partida_categoria": "Materiales",
    "concepto": "Repintar muro por error de color",
    "monto_solicitado": "1500.00",
    "costo_estimado": "1500.00",
    "urgencia": "media",
    "evidencia_url": "https://storage.empresa.com/evidencias/muro.jpg",
}
GASTO_SIN_SOLICITUD = {
    "tipo": "ticket",
    "monto_comprobado": "400.00",
    "fecha_gasto": date.today().isoformat(),
    "proveedor": "Ferretería La Obra",
    "concepto": "Pintura para corregir muro",
    "obra_id": OBRA,
    "etapa_construccion": "acabados",
    "partida_categoria": "Materiales",
}


class BaseContingenciaTestCase(BaseHU07TestCase):
    def pedir_y_aprobar(self, **cuerpo):
        solicitud_id = self.client.post("/api/solicitudes", json=SOLICITUD).json()["solicitud"]["id"]
        return self.client.post(f"/api/solicitudes/{solicitud_id}/aprobar", json={**ADMINISTRACION, **cuerpo})

    def comprobar(self, clasificacion, monto, cerrar=True):
        """Comprueba un gasto de una solicitud aprobada con la clasificación indicada."""
        self.solicitud = crear_solicitud_aprobada(partida="Materiales", clasificacion=clasificacion)
        comprobante_id = self.capturar().json()["id"]
        respuesta = self.completar(comprobante_id, tipo="factura", monto_comprobado=monto, horas=None, unidad_horas=None)
        self.assertEqual(respuesta.status_code, 200)
        if cerrar:
            self.assertEqual(self.cerrar(comprobante_id).status_code, 200)
        return comprobante_id

    def saldo(self):
        return next(s for s in self.client.get("/api/saldos").json() if s["obra_id"] == OBRA)


class TestHU15Clasificacion(BaseContingenciaTestCase):
    def test_criterio_1_aprobar_exige_elegir_cobrable_o_contingencia(self):
        """Dado que registro un gasto, cuando lo clasifico, entonces debo elegir entre
        "cobrable al cliente" o "fondo de contingencia"."""
        sin_clasificar = self.pedir_y_aprobar()
        invalida = self.pedir_y_aprobar(clasificacion="otra")

        self.assertEqual(sin_clasificar.status_code, 422)
        self.assertIn("fondo de contingencia", str(sin_clasificar.json()["detail"]))
        self.assertEqual(invalida.status_code, 422)

    def test_clasificacion_queda_registrada_en_la_autorizacion(self):
        respuesta = self.pedir_y_aprobar(clasificacion="fondo_contingencia")

        self.assertEqual(respuesta.status_code, 200)
        solicitud_id = respuesta.json()["id"]
        consultada = self.client.get(f"/api/solicitudes/{solicitud_id}").json()
        self.assertEqual(consultada["autorizacion"]["clasificacion"], "fondo_contingencia")

    def test_rechazo_no_lleva_clasificacion(self):
        solicitud_id = self.client.post("/api/solicitudes", json=SOLICITUD).json()["solicitud"]["id"]

        respuesta = self.client.post(
            f"/api/solicitudes/{solicitud_id}/rechazar",
            json={**ADMINISTRACION, "comentario": "No corresponde a esta etapa."},
        )

        self.assertEqual(respuesta.status_code, 200)
        self.assertIsNone(respuesta.json()["autorizacion"]["clasificacion"])

    def test_comprobante_hereda_la_clasificacion_de_la_solicitud(self):
        self.solicitud = crear_solicitud_aprobada(partida="Materiales", clasificacion="fondo_contingencia")

        capturado = self.capturar(solicitud_id=self.solicitud.id).json()
        sin_vincular = self.capturar().json()
        completado = self.completar(sin_vincular["id"], horas=None, unidad_horas=None).json()

        self.assertEqual(capturado["clasificacion"], "fondo_contingencia")
        self.assertIsNone(sin_vincular["clasificacion"])
        self.assertEqual(completado["clasificacion"], "fondo_contingencia")

    def test_gasto_sin_solicitud_exige_clasificacion(self):
        comprobante_id = self.capturar().json()["id"]
        url = f"/api/comprobantes/{comprobante_id}/datos"

        sin_clasificar = self.client.put(url, json=GASTO_SIN_SOLICITUD)
        clasificado = self.client.put(url, json={**GASTO_SIN_SOLICITUD, "clasificacion": "fondo_contingencia"})

        self.assertEqual(sin_clasificar.status_code, 422)
        self.assertIn("fondo de contingencia", sin_clasificar.json()["detail"])
        self.assertEqual(clasificado.status_code, 200)
        self.assertEqual(clasificado.json()["clasificacion"], "fondo_contingencia")
        self.assertEqual(clasificado.json()["datos"]["clasificacion"], "fondo_contingencia")


class TestHU15SaldoContingencia(BaseContingenciaTestCase):
    def test_obra_sin_gastos_tiene_todo_el_fondo_disponible(self):
        saldo = self.saldo()

        self.assertEqual(Decimal(saldo["fondo_contingencia"]), FONDO_CONTINGENCIA)
        self.assertEqual(Decimal(saldo["disponible_contingencia"]), FONDO_CONTINGENCIA)

    def test_criterio_2_gasto_de_contingencia_actualiza_el_disponible(self):
        """Dado que un gasto se carga al fondo de contingencia, cuando se guarda,
        entonces el saldo disponible del fondo de la obra se actualiza."""
        self.comprobar("fondo_contingencia", "1200.00")

        saldo = self.saldo()

        self.assertEqual(Decimal(saldo["gasto_contingencia"]), Decimal("1200.00"))
        self.assertEqual(Decimal(saldo["disponible_contingencia"]), FONDO_CONTINGENCIA - Decimal("1200.00"))
        self.assertEqual(Decimal(saldo["gasto_cobrable_cliente"]), Decimal("0"))

    def test_gasto_cobrable_no_toca_el_fondo_y_se_suma_para_facturar(self):
        self.comprobar("cobrable_cliente", "900.00")

        saldo = self.saldo()

        self.assertEqual(Decimal(saldo["gasto_cobrable_cliente"]), Decimal("900.00"))
        self.assertEqual(Decimal(saldo["disponible_contingencia"]), FONDO_CONTINGENCIA)

    def test_gasto_sin_solicitud_de_contingencia_tambien_descuenta(self):
        comprobante_id = self.capturar().json()["id"]
        self.client.put(
            f"/api/comprobantes/{comprobante_id}/datos",
            json={**GASTO_SIN_SOLICITUD, "clasificacion": "fondo_contingencia"},
        )
        self.cerrar(comprobante_id)

        self.assertEqual(Decimal(self.saldo()["gasto_contingencia"]), Decimal("400.00"))

    def test_borrador_no_descuenta_hasta_guardarse(self):
        self.comprobar("fondo_contingencia", "1200.00", cerrar=False)

        self.assertEqual(Decimal(self.saldo()["disponible_contingencia"]), FONDO_CONTINGENCIA)

    def test_exceder_el_fondo_deja_el_disponible_negativo(self):
        self.comprobar("fondo_contingencia", "3500.00")
        self.comprobar("fondo_contingencia", "3500.00")

        self.assertEqual(
            Decimal(self.saldo()["disponible_contingencia"]), FONDO_CONTINGENCIA - Decimal("7000.00")
        )

    def test_reverso_devuelve_el_monto_al_fondo(self):
        comprobante_id = self.comprobar("fondo_contingencia", "1200.00")

        self.client.post(
            f"/api/comprobantes/{comprobante_id}/ajustes",
            json={"tipo_registro": "reverso", "motivo": "Factura cancelada por el proveedor"},
        )

        self.assertEqual(Decimal(self.saldo()["disponible_contingencia"]), FONDO_CONTINGENCIA)

    def test_ajuste_conserva_la_clasificacion_del_original(self):
        comprobante_id = self.comprobar("fondo_contingencia", "1200.00")
        datos = {
            "tipo": "factura", "monto_comprobado": "1000.00", "fecha_gasto": date.today().isoformat(),
            "proveedor": "Pinturas del Centro", "concepto": "Pintura corregida",
        }

        ajuste = self.client.post(
            f"/api/comprobantes/{comprobante_id}/ajustes",
            json={"tipo_registro": "ajuste", "motivo": "Monto mal capturado", "datos": datos},
        )

        self.assertEqual(ajuste.status_code, 201)
        self.assertEqual(ajuste.json()["clasificacion"], "fondo_contingencia")
        # El ajuste queda en revisión de contabilidad y sustituye al original en el saldo
        self.assertEqual(Decimal(self.saldo()["gasto_contingencia"]), Decimal("1000.00"))


class TestMigracionColumnas(unittest.TestCase):
    def test_agrega_columna_nueva_a_una_tabla_existente_sin_borrar_datos(self):
        motor = create_engine("sqlite://", poolclass=StaticPool, connect_args={"check_same_thread": False})
        with motor.begin() as conexion:
            # Tabla creada por una versión anterior, sin la columna de clasificación
            conexion.execute(text(
                "CREATE TABLE autorizaciones (id INTEGER PRIMARY KEY, solicitud_id CHAR(32), decision VARCHAR(20), "
                "autorizador_id VARCHAR(60), autorizador_nombre VARCHAR(120), rol_autorizador VARCHAR(20), "
                "monto_autorizado NUMERIC(14, 2), comentario TEXT, fecha_decision DATETIME)"
            ))
            conexion.execute(text("INSERT INTO autorizaciones (id, decision) VALUES (1, 'Aprobada')"))

        agregar_columnas_faltantes(motor)
        agregar_columnas_faltantes(motor)  # Repetirlo no debe fallar

        columnas = {c["name"] for c in inspect(motor).get_columns("autorizaciones")}
        self.assertIn("clasificacion", columnas)
        with motor.connect() as conexion:
            self.assertEqual(conexion.execute(text("SELECT COUNT(*) FROM autorizaciones")).scalar(), 1)


if __name__ == "__main__":
    unittest.main()
