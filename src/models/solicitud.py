"""Modelos y esquemas de datos para el Requerimiento RF01 e Historia HU01.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, Field, field_validator


class EtapaConstruccion(str, Enum):
    CIMENTACION = "cimentación"
    ESTRUCTURA = "estructura"
    ALBANILERIA = "albañilería"
    INSTALACIONES = "instalaciones"
    ACABADOS = "acabados"
    ENTREGA = "entrega"


class UrgenciaSolicitud(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"
    URGENTE = "urgente"


class EstadoSolicitud(str, Enum):
    PENDIENTE = "Pendiente"
    APROBADO = "Aprobado"
    RECHAZADO = "Rechazado"
    RECONCILIADO = "Reconciliado"


class SolicitudFondoBase(BaseModel):
    obra_id: str = Field(..., description="Identificador de la obra activa")
    solicitante_id: str = Field(..., description="Identificador del residente de obra solicitante")
    etapa_construccion: EtapaConstruccion = Field(..., description="Etapa constructiva")
    partida_categoria: str = Field(..., min_length=1, description="Partida o categoría del gasto")
    concepto: str = Field(..., min_length=3, description="Concepto detallado de la compra o servicio")
    monto_solicitado: Decimal = Field(..., gt=0, description="Monto solicitado en moneda local")
    costo_estimado: Decimal = Field(..., gt=0, description="Costo estimado de la actividad")
    urgencia: UrgenciaSolicitud = Field(..., description="Nivel de urgencia")
    evidencia_url: str = Field(..., min_length=5, description="URL o ruta de la evidencia que justifica la necesidad")

    @field_validator("evidencia_url")
    @classmethod
    def validar_evidencia_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La evidencia de la necesidad es obligatoria para registrar la solicitud.")
        return v.strip()


class SolicitudFondoCreate(SolicitudFondoBase):
    firma_digital_direccion: Optional[str] = Field(
        default=None,
        description="Firma digital obligatoria si el monto requiere aprobación de Dirección"
    )


class NotificacionNivelAutorizacion(BaseModel):
    destinatario_rol: str
    mensaje: str
    folio: str
    monto: Decimal
    timestamp: datetime = Field(default_factory=datetime.utcnow)


class SolicitudFondo(SolicitudFondoBase):
    id: UUID = Field(default_factory=uuid4, description="UUID identificador del registro")
    folio: str = Field(..., description="Folio único y legible generado automáticamente")
    firma_digital_direccion: Optional[str] = Field(default=None, description="Firma digital proporcionada para montos altos")
    estado: EstadoSolicitud = Field(default=EstadoSolicitud.PENDIENTE, description="Estado de la solicitud")
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")
    deleted_at: Optional[datetime] = Field(default=None, description="Fecha de borrado lógico")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de última actualización")


class SolicitudFondoResponse(BaseModel):
    solicitud: SolicitudFondo
    notificacion_enviada: NotificacionNivelAutorizacion
