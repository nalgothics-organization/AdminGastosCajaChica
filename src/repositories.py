"""Repositorios que guardan los modelos de negocio en la base de datos.

Exponen la misma interfaz mínima que tenía el almacén en memoria (`get`, `values`, `[]`) más
`guardar`, que los servicios llaman después de cada cambio. Nunca borran filas: el borrado es lógico.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from datetime import datetime, timezone
from typing import List, Optional
from uuid import UUID

from sqlalchemy import func, select

from src.database import AutorizacionTabla, ComprobanteTabla, EntregaTabla, SessionLocal, SolicitudTabla
from src.models.comprobante import Comprobante, ComprobanteDatos, LecturaComprobante
from src.models.solicitud import Autorizacion, Entrega, SolicitudFondo


def _utc(valor: Optional[datetime]) -> Optional[datetime]:
    """SQLite devuelve fechas sin zona horaria; todo lo que se guarda está en UTC."""
    if valor is not None and valor.tzinfo is None:
        return valor.replace(tzinfo=timezone.utc)
    return valor


def _valor(enum_o_texto):
    return getattr(enum_o_texto, "value", enum_o_texto)


class SolicitudRepositorio:
    def get(self, solicitud_id: UUID) -> Optional[SolicitudFondo]:
        with SessionLocal() as sesion:
            fila = sesion.get(SolicitudTabla, solicitud_id)
            return self._a_modelo(fila) if fila else None

    def __getitem__(self, solicitud_id: UUID) -> SolicitudFondo:
        solicitud = self.get(solicitud_id)
        if solicitud is None:
            raise KeyError(solicitud_id)
        return solicitud

    def values(self) -> List[SolicitudFondo]:
        with SessionLocal() as sesion:
            filas = sesion.scalars(select(SolicitudTabla).order_by(SolicitudTabla.created_at, SolicitudTabla.folio))
            return [self._a_modelo(f) for f in filas.unique()]

    def total(self) -> int:
        """Cantidad de solicitudes registradas, incluidas las borradas lógicamente."""
        with SessionLocal() as sesion:
            return sesion.scalar(select(func.count()).select_from(SolicitudTabla)) or 0

    def guardar(self, solicitud: SolicitudFondo) -> SolicitudFondo:
        with SessionLocal() as sesion, sesion.begin():
            fila = sesion.get(SolicitudTabla, solicitud.id) or SolicitudTabla(id=solicitud.id)
            fila.folio = solicitud.folio
            fila.obra_id = solicitud.obra_id
            fila.solicitante_id = solicitud.solicitante_id
            fila.etapa_construccion = _valor(solicitud.etapa_construccion)
            fila.partida_categoria = solicitud.partida_categoria
            fila.concepto = solicitud.concepto
            fila.monto_solicitado = solicitud.monto_solicitado
            fila.costo_estimado = solicitud.costo_estimado
            fila.urgencia = _valor(solicitud.urgencia)
            fila.evidencia_url = solicitud.evidencia_url
            fila.firma_digital_direccion = solicitud.firma_digital_direccion
            fila.nivel_autorizacion = solicitud.nivel_autorizacion
            fila.estado = _valor(solicitud.estado)
            fila.activo = solicitud.activo
            fila.deleted_at = solicitud.deleted_at
            fila.created_at = solicitud.created_at
            fila.updated_at = solicitud.updated_at

            # La autorización se inserta una sola vez y no se vuelve a modificar
            if solicitud.autorizacion and fila.autorizacion is None:
                decision = solicitud.autorizacion
                fila.autorizacion = AutorizacionTabla(
                    decision=_valor(decision.decision),
                    autorizador_id=decision.autorizador_id,
                    autorizador_nombre=decision.autorizador_nombre,
                    rol_autorizador=_valor(decision.rol_autorizador),
                    monto_autorizado=decision.monto_autorizado,
                    comentario=decision.comentario,
                    fecha_decision=decision.fecha_decision,
                )

            # La entrega también se inserta una sola vez (RF06)
            if solicitud.entrega and fila.entrega is None:
                entrega = solicitud.entrega
                fila.entrega = EntregaTabla(
                    forma_entrega=_valor(entrega.forma_entrega),
                    fecha_entrega=entrega.fecha_entrega,
                    referencia=entrega.referencia,
                    entregado_por_id=entrega.entregado_por_id,
                    entregado_por_nombre=entrega.entregado_por_nombre,
                    rol_entrega=_valor(entrega.rol_entrega),
                    fecha_registro=entrega.fecha_registro,
                )
            sesion.add(fila)
        return solicitud

    def __setitem__(self, solicitud_id: UUID, solicitud: SolicitudFondo) -> None:
        self.guardar(solicitud)

    @staticmethod
    def _a_modelo(fila: SolicitudTabla) -> SolicitudFondo:
        autorizacion = None
        if fila.autorizacion:
            a = fila.autorizacion
            autorizacion = Autorizacion(
                decision=a.decision,
                autorizador_id=a.autorizador_id,
                autorizador_nombre=a.autorizador_nombre,
                rol_autorizador=a.rol_autorizador,
                monto_autorizado=a.monto_autorizado,
                comentario=a.comentario,
                fecha_decision=_utc(a.fecha_decision),
            )
        entrega = None
        if fila.entrega:
            e = fila.entrega
            entrega = Entrega(
                forma_entrega=e.forma_entrega,
                fecha_entrega=e.fecha_entrega,
                referencia=e.referencia,
                entregado_por_id=e.entregado_por_id,
                entregado_por_nombre=e.entregado_por_nombre,
                rol_entrega=e.rol_entrega,
                fecha_registro=_utc(e.fecha_registro),
            )
        return SolicitudFondo(
            id=fila.id,
            folio=fila.folio,
            obra_id=fila.obra_id,
            solicitante_id=fila.solicitante_id,
            etapa_construccion=fila.etapa_construccion,
            partida_categoria=fila.partida_categoria,
            concepto=fila.concepto,
            monto_solicitado=fila.monto_solicitado,
            costo_estimado=fila.costo_estimado,
            urgencia=fila.urgencia,
            evidencia_url=fila.evidencia_url,
            firma_digital_direccion=fila.firma_digital_direccion,
            nivel_autorizacion=fila.nivel_autorizacion,
            estado=fila.estado,
            autorizacion=autorizacion,
            entrega=entrega,
            activo=fila.activo,
            deleted_at=_utc(fila.deleted_at),
            created_at=_utc(fila.created_at),
            updated_at=_utc(fila.updated_at),
        )


class ComprobanteRepositorio:
    def get(self, comprobante_id: UUID) -> Optional[Comprobante]:
        with SessionLocal() as sesion:
            fila = sesion.get(ComprobanteTabla, comprobante_id)
            return self._a_modelo(fila) if fila else None

    def __getitem__(self, comprobante_id: UUID) -> Comprobante:
        comprobante = self.get(comprobante_id)
        if comprobante is None:
            raise KeyError(comprobante_id)
        return comprobante

    def values(self) -> List[Comprobante]:
        with SessionLocal() as sesion:
            filas = sesion.scalars(select(ComprobanteTabla).order_by(ComprobanteTabla.created_at))
            return [self._a_modelo(f) for f in filas]

    def guardar(self, comprobante: Comprobante) -> Comprobante:
        with SessionLocal() as sesion, sesion.begin():
            fila = sesion.get(ComprobanteTabla, comprobante.id) or ComprobanteTabla(id=comprobante.id)
            fila.solicitante_id = comprobante.solicitante_id
            fila.solicitud_id = comprobante.solicitud_id
            fila.comprobante_origen_id = comprobante.comprobante_origen_id
            fila.tipo_registro = _valor(comprobante.tipo_registro)
            fila.motivo_correccion = comprobante.motivo_correccion
            fila.estado = _valor(comprobante.estado)
            fila.imagen_ruta = comprobante.imagen_ruta
            fila.requiere_horas = comprobante.requiere_horas
            fila.obra_id = comprobante.obra_id
            fila.etapa_construccion = _valor(comprobante.etapa_construccion)
            fila.partida_categoria = comprobante.partida_categoria

            datos = comprobante.datos
            fila.tipo = _valor(datos.tipo) if datos else None
            fila.monto_comprobado = datos.monto_comprobado if datos else None
            fila.fecha_gasto = datos.fecha_gasto if datos else None
            fila.proveedor = datos.proveedor if datos else None
            fila.concepto = datos.concepto if datos else None
            fila.horas = datos.horas if datos else None
            fila.unidad_horas = _valor(datos.unidad_horas) if datos else None
            fila.lectura = comprobante.lectura.model_dump(mode="json") if comprobante.lectura else None
            fila.cierre_automatico = comprobante.cierre_automatico

            fila.activo = comprobante.activo
            fila.deleted_at = comprobante.deleted_at
            fila.created_at = comprobante.created_at
            fila.updated_at = comprobante.updated_at
            sesion.add(fila)
        return comprobante

    def __setitem__(self, comprobante_id: UUID, comprobante: Comprobante) -> None:
        self.guardar(comprobante)

    @staticmethod
    def _a_modelo(fila: ComprobanteTabla) -> Comprobante:
        datos = None
        if fila.tipo is not None:
            sin_solicitud = fila.solicitud_id is None
            datos = ComprobanteDatos(
                tipo=fila.tipo,
                monto_comprobado=fila.monto_comprobado,
                fecha_gasto=fila.fecha_gasto,
                proveedor=fila.proveedor,
                concepto=fila.concepto,
                horas=fila.horas,
                unidad_horas=fila.unidad_horas,
                solicitud_id=fila.solicitud_id,
                # La clasificación solo viaja en los datos cuando no la aporta una solicitud
                obra_id=fila.obra_id if sin_solicitud else None,
                etapa_construccion=fila.etapa_construccion if sin_solicitud else None,
                partida_categoria=fila.partida_categoria if sin_solicitud else None,
            )
        return Comprobante(
            id=fila.id,
            solicitante_id=fila.solicitante_id,
            solicitud_id=fila.solicitud_id,
            requiere_horas=fila.requiere_horas,
            obra_id=fila.obra_id,
            etapa_construccion=fila.etapa_construccion,
            partida_categoria=fila.partida_categoria,
            imagen_ruta=fila.imagen_ruta,
            estado=fila.estado,
            tipo_registro=fila.tipo_registro,
            comprobante_origen_id=fila.comprobante_origen_id,
            motivo_correccion=fila.motivo_correccion,
            datos=datos,
            lectura=LecturaComprobante(**fila.lectura) if fila.lectura else None,
            cierre_automatico=fila.cierre_automatico,
            activo=fila.activo,
            deleted_at=_utc(fila.deleted_at),
            created_at=_utc(fila.created_at),
            updated_at=_utc(fila.updated_at),
        )
