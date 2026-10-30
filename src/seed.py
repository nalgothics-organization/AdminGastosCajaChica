"""Carga datos de ejemplo para la demostración del prototipo.

Uso: python -m src.seed [--reset]
Sin --reset no hace nada si la base de datos ya tiene solicitudes.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import os
import struct
import sys
import zlib
from datetime import date, timedelta
from decimal import Decimal

from src.database import crear_tablas, reiniciar_tablas
from src.models.comprobante import ComprobanteDatos
from src.models.solicitud import AprobacionCreate, RechazoCreate, SolicitudFondoCreate
from src.services.comprobante_service import comprobante_service
from src.services.solicitud_service import solicitud_service

EVIDENCIA = "https://storage.empresa.com/evidencias/"


def imagen_demo() -> bytes:
    """PNG válido de ~30 KB (ruido aleatorio) para cumplir el tamaño mínimo de legibilidad."""
    ancho = alto = 100
    filas = b"".join(b"\x00" + os.urandom(ancho * 3) for _ in range(alto))

    def bloque(tipo: bytes, datos: bytes) -> bytes:
        crc = zlib.crc32(tipo + datos) & 0xFFFFFFFF
        return struct.pack(">I", len(datos)) + tipo + datos + struct.pack(">I", crc)

    cabecera = struct.pack(">IIBBBBB", ancho, alto, 8, 2, 0, 0, 0)
    return (
        b"\x89PNG\r\n\x1a\n"
        + bloque(b"IHDR", cabecera)
        + bloque(b"IDAT", zlib.compress(filas, 0))
        + bloque(b"IEND", b"")
    )


def solicitar(obra, residente, etapa, partida, concepto, monto, costo, urgencia, evidencia, firma=None):
    return solicitud_service.crear_solicitud(
        SolicitudFondoCreate(
            obra_id=obra,
            solicitante_id=residente,
            etapa_construccion=etapa,
            partida_categoria=partida,
            concepto=concepto,
            monto_solicitado=Decimal(monto),
            costo_estimado=Decimal(costo),
            urgencia=urgencia,
            evidencia_url=EVIDENCIA + evidencia,
            firma_digital_direccion=firma,
        )
    ).solicitud


def aprobar(solicitud, nombre, rol, comentario=None, monto=None):
    solicitud_service.aprobar_solicitud(
        solicitud.id,
        AprobacionCreate(
            autorizador_id=f"{rol[:3].upper()}-{nombre.split()[0].upper()}",
            autorizador_nombre=nombre,
            rol_autorizador=rol,
            comentario=comentario,
            monto_autorizado=Decimal(monto) if monto else None,
        ),
    )


def comprobar(residente, datos: ComprobanteDatos, cerrar=True):
    comprobante = comprobante_service.capturar_rapido(residente, imagen_demo(), "image/png")
    comprobante_service.completar_datos(comprobante.id, datos)
    if cerrar:
        comprobante_service.cerrar(comprobante.id)
    return comprobante


def cargar() -> None:
    hoy = date.today()

    # Aprobadas y con gasto comprobado
    maquinaria = solicitar(
        "OBRA-NORTE-01", "RESIDENTE-PAU", "cimentación", "Renta de Maquinaria",
        "Renta de retroexcavadora para sondeo", "3500.00", "4000.00", "urgente", "fuga_tubo_01.jpg",
    )
    aprobar(maquinaria, "Laura Méndez", "Administración", "Se autoriza el monto cotizado.")
    comprobar("RESIDENTE-PAU", ComprobanteDatos(
        tipo="nota_simple", monto_comprobado=Decimal("3200.00"), fecha_gasto=hoy - timedelta(days=1),
        proveedor="Maquinaria El Güero", concepto="Renta de retroexcavadora",
        horas=Decimal("4.5"), unidad_horas="maquinaria",
    ))

    pintura = solicitar(
        "OBRA-SUR-02", "RESIDENTE-JP", "acabados", "Materiales",
        "Compra de pintura y selladores para fachada", "18000.00", "18500.00", "alta", "fachada_02.jpg",
        firma="FIRMA-DIR-001",
    )
    aprobar(pintura, "Carlos Ruiz", "Dirección", "Aprobado dentro del presupuesto de acabados.")
    comprobar("RESIDENTE-JP", ComprobanteDatos(
        tipo="factura", monto_comprobado=Decimal("12400.00"), fecha_gasto=hoy - timedelta(days=2),
        proveedor="Pinturas del Centro", concepto="Pintura vinílica y sellador",
    ))
    # Una foto tomada en obra que todavía no se completa
    comprobante_service.capturar_rapido("RESIDENTE-JP", imagen_demo(), "image/png")

    # Esperando decisión: una de Administración y una de Dirección
    solicitar(
        "OBRA-NORTE-01", "RESIDENTE-PAU", "estructura", "Materiales",
        "Compra de grava y arena", "1200.00", "1300.00", "media", "grava_03.jpg",
    )
    solicitar(
        "OBRA-SUR-02", "RESIDENTE-JP", "instalaciones", "Mano de Obra",
        "Cuadrilla de plomería por dos semanas", "7500.00", "8000.00", "alta", "plomeria_04.jpg",
        firma="FIRMA-DIR-002",
    )

    # Rechazada, con el comentario de quien la decidió
    equipo = solicitar(
        "OBRA-NORTE-01", "RESIDENTE-LUIS", "acabados", "Otros",
        "Compra de herramienta eléctrica", "2000.00", "2000.00", "baja", "herramienta_05.jpg",
    )
    solicitud_service.rechazar_solicitud(
        equipo.id,
        RechazoCreate(
            autorizador_id="ADM-LAURA", autorizador_nombre="Laura Méndez", rol_autorizador="Administración",
            comentario="La herramienta ya está en el almacén de la obra.",
        ),
    )

    # Gasto que un residente pagó de su bolsillo sin solicitud previa: reembolso pendiente
    comprobar("RESIDENTE-LUIS", ComprobanteDatos(
        tipo="ticket", monto_comprobado=Decimal("850.00"), fecha_gasto=hoy,
        proveedor="Ferretería La Obra", concepto="Cemento y varilla urgentes",
        obra_id="OBRA-SUR-02", etapa_construccion="estructura", partida_categoria="Materiales",
    ))


def main() -> None:
    if "--reset" in sys.argv:
        reiniciar_tablas()
    else:
        crear_tablas()
    if solicitud_service.listar_solicitudes_activas():
        print("La base de datos ya tiene solicitudes; no se cargaron datos de ejemplo (usa --reset).")
        return
    cargar()
    print("Datos de ejemplo cargados: 5 solicitudes, 4 comprobantes en 2 obras.")


if __name__ == "__main__":
    main()
