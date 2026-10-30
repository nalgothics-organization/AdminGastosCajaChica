"""Saldos por obra en tiempo real (RF10/HU10).

El saldo se calcula al consultarlo a partir de las solicitudes aprobadas y de los comprobantes
cerrados, así que siempre refleja el último movimiento.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from decimal import Decimal
from typing import Dict, List

from pydantic import BaseModel, Field

from src.models.comprobante import ESTADOS_CERRADOS, Comprobante, TipoRegistro
from src.models.solicitud import EstadoSolicitud
from src.services.comprobante_service import ComprobanteService, comprobante_service
from src.services.obra_catalogo import OBRAS
from src.services.solicitud_service import SolicitudFondoService, solicitud_service

CERO = Decimal("0.00")


class SaldoObra(BaseModel):
    obra_id: str
    nombre: str = ""
    presupuesto_caja_chica: Decimal = Field(default=CERO, description="Fondo de caja chica asignado a la obra")
    autorizado: Decimal = Field(default=CERO, description="Suma de los montos autorizados de solicitudes aprobadas")
    disponible_caja_chica: Decimal = Field(
        default=CERO, description="Fondo de caja chica menos lo autorizado; negativo si se excedió"
    )
    porcentaje_autorizado: Decimal = Field(default=CERO, description="Autorizado entre el fondo, de 0 a 100 o más")
    comprobado: Decimal = Field(default=CERO, description="Gasto comprobado contra solicitudes aprobadas")
    por_comprobar: Decimal = Field(default=CERO, description="Autorizado menos comprobado; negativo si se excedió")
    gasto_sin_solicitud: Decimal = Field(
        default=CERO, description="Gasto pagado por el residente sin solicitud previa; es un reembolso pendiente"
    )
    pendiente_autorizacion: Decimal = Field(default=CERO, description="Monto de solicitudes que esperan decisión")
    solicitudes_pendientes: int = 0
    comprobantes_en_revision: int = 0
    porcentaje_gastado: Decimal = Field(default=CERO, description="Comprobado entre autorizado, de 0 a 100 o más")


class SaldoService:
    def __init__(
        self,
        solicitudes: SolicitudFondoService = solicitud_service,
        comprobantes: ComprobanteService = comprobante_service,
    ):
        self._solicitudes = solicitudes
        self._comprobantes = comprobantes

    @staticmethod
    def _comprobantes_vigentes(cerrados: List[Comprobante]) -> List[Comprobante]:
        """Un ajuste sustituye al original y un reverso lo anula; el reverso mismo no suma gasto."""
        corregidos = {
            c.comprobante_origen_id
            for c in cerrados
            if c.tipo_registro in (TipoRegistro.AJUSTE, TipoRegistro.REVERSO)
        }
        return [
            c for c in cerrados
            if c.tipo_registro == TipoRegistro.AJUSTE
            or (c.tipo_registro == TipoRegistro.ORIGINAL and c.id not in corregidos)
        ]

    def por_obra(self) -> List[SaldoObra]:
        # Todas las obras del catálogo aparecen aunque no tengan movimientos
        saldos: Dict[str, SaldoObra] = {
            o.id: SaldoObra(obra_id=o.id, nombre=o.nombre, presupuesto_caja_chica=o.presupuesto_caja_chica)
            for o in OBRAS
        }

        def saldo_de(obra_id: str) -> SaldoObra:
            return saldos.setdefault(obra_id, SaldoObra(obra_id=obra_id, nombre=obra_id))

        for solicitud in self._solicitudes.listar_solicitudes_activas():
            saldo = saldo_de(solicitud.obra_id)
            if solicitud.estado == EstadoSolicitud.APROBADO and solicitud.autorizacion:
                saldo.autorizado += solicitud.autorizacion.monto_autorizado or CERO
            elif solicitud.estado == EstadoSolicitud.PENDIENTE:
                saldo.pendiente_autorizacion += solicitud.monto_solicitado
                saldo.solicitudes_pendientes += 1

        cerrados = [
            c for c in self._comprobantes.listar()
            if c.estado in ESTADOS_CERRADOS and c.datos is not None and c.obra_id
        ]
        for comprobante in self._comprobantes_vigentes(cerrados):
            saldo = saldo_de(comprobante.obra_id)
            if comprobante.solicitud_id is None:
                saldo.gasto_sin_solicitud += comprobante.datos.monto_comprobado
            else:
                saldo.comprobado += comprobante.datos.monto_comprobado

        for comprobante in cerrados:
            if comprobante.estado.value == "Revisión contabilidad" and comprobante.tipo_registro != TipoRegistro.REVERSO:
                saldo_de(comprobante.obra_id).comprobantes_en_revision += 1

        for saldo in saldos.values():
            saldo.por_comprobar = saldo.autorizado - saldo.comprobado
            saldo.disponible_caja_chica = saldo.presupuesto_caja_chica - saldo.autorizado
            if saldo.presupuesto_caja_chica > 0:
                saldo.porcentaje_autorizado = (
                    saldo.autorizado * 100 / saldo.presupuesto_caja_chica
                ).quantize(Decimal("0.1"))
            if saldo.autorizado > 0:
                saldo.porcentaje_gastado = (saldo.comprobado * 100 / saldo.autorizado).quantize(Decimal("0.1"))
        return sorted(saldos.values(), key=lambda s: s.obra_id)


saldo_service = SaldoService()
