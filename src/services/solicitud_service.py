"""Módulo de servicios de negocio para la gestión de Solicitudes de Fondo.
Implementa:
- Generación automática de folio único (RF01/HU01).
- Reglas de notificación al nivel correspondiente (HU01).
- Soft delete e inmutabilidad según AGENTS.md.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional
from uuid import UUID

from src.models.solicitud import (
    EstadoSolicitud,
    NotificacionNivelAutorizacion,
    SolicitudFondo,
    SolicitudFondoCreate,
    SolicitudFondoResponse,
)


class SolicitudFondoService:
    def __init__(self):
        # Almacén en memoria simulado para persistencia
        self._db: Dict[UUID, SolicitudFondo] = {}
        self._secuencia_folio: int = 1000
        self.notificaciones_enviadas: List[NotificacionNivelAutorizacion] = []

    def generar_folio_unico(self, obra_id: str) -> str:
        """Genera un folio único, legible y trazable por obra."""
        self._secuencia_folio += 1
        prefijo_obra = obra_id.strip().upper().replace(" ", "")[:4]
        timestamp = datetime.utcnow().strftime("%Y%m")
        return f"SOL-{prefijo_obra}-{timestamp}-{self._secuencia_folio}"

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
            estado=EstadoSolicitud.PENDIENTE,
            activo=True,
        )

        self._db[nueva_solicitud.id] = nueva_solicitud

        # Notificación al nivel autorizador correspondiente (Criterio 2 HU01)
        rol_autorizador = self.determinar_nivel_autorizacion(data.monto_solicitado)
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

    def soft_delete(self, solicitud_id: UUID) -> bool:
        """Regla de Negocio Sección 8: Prohibido hard delete, solo soft delete."""
        solicitud = self._db.get(solicitud_id)
        if not solicitud or not solicitud.activo:
            return False

        solicitud.activo = False
        solicitud.deleted_at = datetime.utcnow()
        solicitud.updated_at = datetime.utcnow()
        return True


# Instancia singleton del servicio
solicitud_service = SolicitudFondoService()
