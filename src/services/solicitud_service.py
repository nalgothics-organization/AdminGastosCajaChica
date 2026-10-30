"""Módulo de servicios de negocio para la gestión de Solicitudes de Fondo.
Implementa:
- Generación automática de folio único (RF01/HU01).
- Reglas de notificación al nivel correspondiente (HU01).
- Aprobación y rechazo con trazabilidad del autorizador (RF05/HU05).
- Soft delete e inmutabilidad según AGENTS.md.
"""

from datetime import datetime, timezone
from decimal import Decimal
from typing import List, Optional
from uuid import UUID

from src.models.solicitud import (
    AprobacionCreate,
    Autorizacion,
    DecisionAutorizacion,
    DecisionBase,
    EstadoSolicitud,
    NotificacionNivelAutorizacion,
    RechazoCreate,
    RolAutorizador,
    SolicitudFondo,
    SolicitudFondoCreate,
    SolicitudFondoResponse,
)
from src.repositories import SolicitudRepositorio


class SolicitudNoEncontradaError(LookupError):
    pass


class SolicitudNoPendienteError(Exception):
    """La solicitud ya fue decidida; las correcciones se registran como ajuste (AGENTS.md §8)."""


class AutorizadorNoPermitidoError(Exception):
    """El rol del autorizador no alcanza el nivel que exige el monto de la solicitud."""


class SolicitudFondoService:
    def __init__(self):
        self._db = SolicitudRepositorio()
        self.notificaciones_enviadas: List[NotificacionNivelAutorizacion] = []

    def generar_folio_unico(self, obra_id: str) -> str:
        """Genera un folio único, legible y trazable por obra."""
        # Las solicitudes nunca se borran físicamente, así que el total solo crece y el folio no se repite
        secuencia = 1001 + self._db.total()
        prefijo_obra = obra_id.strip().upper().replace(" ", "")[:4]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m")
        return f"SOL-{prefijo_obra}-{timestamp}-{secuencia}"

    def determinar_nivel_autorizacion(self, monto: Decimal) -> str:
        """Determina el nivel autorizador requerido según el monto (HU03/HU01).
        Límite estándar de administración: 5,000 MXN. Montos superiores requieren Dirección.
        """
        limite_administracion = Decimal("5000.00")
        if monto > limite_administracion:
            return "Dirección"
        return "Administración"

    def emitir_notificacion(self, folio: str, monto: Decimal, rol_destinatario: str) -> NotificacionNivelAutorizacion:
        """Emite la notificación al nivel de autorización correspondiente."""
        mensaje = (
            f"Nueva solicitud de fondo {folio} por un monto de ${monto:.2f} "
            f"requiere autorización del área de {rol_destinatario}."
        )
        notificacion = NotificacionNivelAutorizacion(
            destinatario_rol=rol_destinatario,
            mensaje=mensaje,
            folio=folio,
            monto=monto,
        )
        self.notificaciones_enviadas.append(notificacion)
        return notificacion

    def crear_solicitud(self, data: SolicitudFondoCreate) -> SolicitudFondoResponse:
        """Registra una solicitud de fondo, valida evidencia, genera folio y notifica."""
        # Validación de evidencia requerida (Criterio 1 HU01)
        if not data.evidencia_url or not data.evidencia_url.strip():
            raise ValueError("Es obligatorio adjuntar una evidencia de la necesidad.")

        # Validar nivel de autorización y requerir firma de dirección (HU03)
        rol_autorizador = self.determinar_nivel_autorizacion(data.monto_solicitado)
        if rol_autorizador == "Dirección" and not data.firma_digital_direccion:
            raise ValueError("Se requiere la firma digital de dirección para montos que exceden el límite de administración.")

        folio = self.generar_folio_unico(data.obra_id)

        nueva_solicitud = SolicitudFondo(
            folio=folio,
            obra_id=data.obra_id,
            solicitante_id=data.solicitante_id,
            etapa_construccion=data.etapa_construccion,
            partida_categoria=data.partida_categoria,
            concepto=data.concepto,
            monto_solicitado=data.monto_solicitado,
            costo_estimado=data.costo_estimado,
            urgencia=data.urgencia,
            evidencia_url=data.evidencia_url,
            firma_digital_direccion=data.firma_digital_direccion,  # Guardar firma
            nivel_autorizacion=rol_autorizador,
            estado=EstadoSolicitud.PENDIENTE,
            activo=True,
        )

        self._db[nueva_solicitud.id] = nueva_solicitud

        # Notificación al nivel autorizador correspondiente
        notificacion = self.emitir_notificacion(folio, data.monto_solicitado, rol_autorizador)

        return SolicitudFondoResponse(
            solicitud=nueva_solicitud,
            notificacion_enviada=notificacion,
        )

    def obtener_por_id(self, solicitud_id: UUID) -> Optional[SolicitudFondo]:
        solicitud = self._db.get(solicitud_id)
        if solicitud and solicitud.activo:
            return solicitud
        return None

    def obtener_por_folio(self, folio: str) -> Optional[SolicitudFondo]:
        for solicitud in self._db.values():
            if solicitud.folio == folio and solicitud.activo:
                return solicitud
        return None

    def listar_solicitudes_activas(self) -> List[SolicitudFondo]:
        return [s for s in self._db.values() if s.activo]

    def _obtener_pendiente(self, solicitud_id: UUID, data: DecisionBase) -> SolicitudFondo:
        """Valida que la solicitud exista, siga pendiente y que el rol pueda decidirla (RF05)."""
        solicitud = self.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(f"Solicitud con ID {solicitud_id} no encontrada.")

        if solicitud.estado != EstadoSolicitud.PENDIENTE:
            raise SolicitudNoPendienteError(
                f"La solicitud {solicitud.folio} ya está en estado {solicitud.estado.value} y no puede decidirse de nuevo."
            )

        # Dirección puede decidir cualquier nivel; Administración solo los de su límite
        if solicitud.nivel_autorizacion == RolAutorizador.DIRECCION.value and data.rol_autorizador != RolAutorizador.DIRECCION:
            raise AutorizadorNoPermitidoError(
                f"La solicitud {solicitud.folio} excede el límite de Administración y solo puede decidirla Dirección."
            )
        return solicitud

    def _registrar_decision(
        self,
        solicitud: SolicitudFondo,
        estado: EstadoSolicitud,
        autorizacion: Autorizacion,
    ) -> SolicitudFondo:
        solicitud.estado = estado
        solicitud.autorizacion = autorizacion
        solicitud.updated_at = autorizacion.fecha_decision
        return self._db.guardar(solicitud)

    def aprobar_solicitud(self, solicitud_id: UUID, data: AprobacionCreate) -> SolicitudFondo:
        """Aprueba la solicitud registrando autorizador, fecha y monto final (HU05 criterio 1)."""
        solicitud = self._obtener_pendiente(solicitud_id, data)

        monto_autorizado = data.monto_autorizado if data.monto_autorizado is not None else solicitud.monto_solicitado
        if monto_autorizado > solicitud.monto_solicitado:
            raise ValueError("El monto autorizado no puede ser mayor al monto solicitado.")

        autorizacion = Autorizacion(
            decision=DecisionAutorizacion.APROBADA,
            autorizador_id=data.autorizador_id,
            autorizador_nombre=data.autorizador_nombre,
            rol_autorizador=data.rol_autorizador,
            monto_autorizado=monto_autorizado,
            comentario=data.comentario or None,
        )
        return self._registrar_decision(solicitud, EstadoSolicitud.APROBADO, autorizacion)

    def rechazar_solicitud(self, solicitud_id: UUID, data: RechazoCreate) -> SolicitudFondo:
        """Rechaza la solicitud; el comentario justificativo es obligatorio (HU05 criterio 2)."""
        solicitud = self._obtener_pendiente(solicitud_id, data)

        autorizacion = Autorizacion(
            decision=DecisionAutorizacion.RECHAZADA,
            autorizador_id=data.autorizador_id,
            autorizador_nombre=data.autorizador_nombre,
            rol_autorizador=data.rol_autorizador,
            comentario=data.comentario,
        )
        return self._registrar_decision(solicitud, EstadoSolicitud.RECHAZADO, autorizacion)

    def soft_delete(self, solicitud_id: UUID) -> bool:
        """Regla de Negocio Sección 8: Prohibido hard delete, solo soft delete."""
        solicitud = self._db.get(solicitud_id)
        if not solicitud or not solicitud.activo:
            return False

        solicitud.activo = False
        solicitud.deleted_at = datetime.now(timezone.utc)
        solicitud.updated_at = datetime.now(timezone.utc)
        self._db.guardar(solicitud)
        return True


# Instancia singleton del servicio
solicitud_service = SolicitudFondoService()
