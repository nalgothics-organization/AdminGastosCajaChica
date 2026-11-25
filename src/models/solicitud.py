"""Modelos y esquemas de datos para el Requerimiento RF01 e Historia HU01.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import re
from datetime import datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, ValidationInfo, field_validator

from src.models.obra import es_partida_generica

# Evidencia aceptada: una foto subida a la API o un enlace http(s) sin espacios (lista de permitidos, OWASP)
EVIDENCIA_PERMITIDA = re.compile(r"^(/api/evidencias/[0-9a-f-]{36}\.(jpg|png|webp)|https?://[^\s<>\"']+)$")


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


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


CAMPOS_OBLIGATORIOS = {
    "obra_id": "Debe seleccionar una obra activa; no se permiten gastos sin obra.",
    "solicitante_id": "El solicitante es obligatorio.",
    "partida_categoria": "Debe seleccionar una partida o categoría de gasto.",
}


class SolicitudFondoBase(BaseModel):
    # Los textos se recortan antes de validar para que "   " cuente como vacío
    model_config = ConfigDict(str_strip_whitespace=True)

    obra_id: str = Field(..., description="Identificador de la obra activa")
    solicitante_id: str = Field(..., description="Identificador del residente de obra solicitante")
    etapa_construccion: EtapaConstruccion = Field(..., description="Etapa constructiva")
    partida_categoria: str = Field(..., description="Partida o categoría del gasto")
    concepto: str = Field(..., min_length=3, description="Concepto detallado de la compra o servicio")
    monto_solicitado: Decimal = Field(..., gt=0, description="Monto solicitado en moneda local")
    costo_estimado: Decimal = Field(..., gt=0, description="Costo estimado de la actividad")
    urgencia: UrgenciaSolicitud = Field(..., description="Nivel de urgencia")
    evidencia_url: str = Field(..., min_length=5, description="URL o ruta de la evidencia que justifica la necesidad")

    @field_validator("obra_id")
    @classmethod
    def validar_obra_obligatoria(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("Es obligatorio seleccionar una obra activa.")
        return v.strip()

    @field_validator("partida_categoria")
    @classmethod
    def validar_partida_no_generica(cls, v: str) -> str:
        if not v or not v.strip() or es_partida_generica(v):
            raise ValueError("No se permiten gastos genéricos; seleccione una partida presupuestal.")
        return v.strip()

    @field_validator("evidencia_url")
    @classmethod
    def validar_evidencia_no_vacia(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La evidencia de la necesidad es obligatoria para registrar la solicitud.")
        if not EVIDENCIA_PERMITIDA.match(v.strip()):
            raise ValueError("La evidencia debe ser una foto subida o un enlace que empiece con http:// o https://.")
        return v.strip()

    @field_validator(*CAMPOS_OBLIGATORIOS)
    @classmethod
    def validar_campos_obligatorios(cls, v: str, info: ValidationInfo) -> str:
        if not v:
            raise ValueError(CAMPOS_OBLIGATORIOS[info.field_name])
        return v


class SolicitudFondoCreate(SolicitudFondoBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "obra_id": "OBRA-NORTE-01",
                    "solicitante_id": "RESIDENTE-PAU",
                    "etapa_construccion": "cimentación",
                    "partida_categoria": "Renta de Maquinaria",
                    "concepto": "Renta de retroexcavadora para sondeo",
                    "monto_solicitado": "3500.00",
                    "costo_estimado": "4000.00",
                    "urgencia": "urgente",
                    "evidencia_url": "https://storage.empresa.com/evidencias/fuga_tubo_01.jpg",
                    "firma_digital_direccion": None,
                }
            ]
        }
    )

    firma_digital_direccion: Optional[str] = Field(
        default=None,
        description="Firma digital obligatoria si el monto requiere aprobación de Dirección"
    )


class NotificacionNivelAutorizacion(BaseModel):
    destinatario_rol: str
    mensaje: str
    folio: str
    monto: Decimal
    timestamp: datetime = Field(default_factory=_ahora_utc)


class RolAutorizador(str, Enum):
    ADMINISTRACION = "Administración"
    DIRECCION = "Dirección"


class DecisionAutorizacion(str, Enum):
    APROBADA = "Aprobada"
    RECHAZADA = "Rechazada"


LONGITUD_MINIMA_COMENTARIO_RECHAZO = 5


class DecisionBase(BaseModel):
    """Datos del autorizador que toma la decisión (RF05/HU05)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    autorizador_id: str = Field(..., min_length=1, description="Identificador del usuario autorizador")
    autorizador_nombre: str = Field(..., min_length=3, description="Nombre de quien autoriza o rechaza")
    rol_autorizador: RolAutorizador = Field(..., description="Rol con el que se toma la decisión")


class AprobacionCreate(DecisionBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "autorizador_id": "ADMIN-LAURA",
                    "autorizador_nombre": "Laura Méndez",
                    "rol_autorizador": "Administración",
                    "monto_autorizado": "3000.00",
                    "comentario": "Se autoriza el monto cotizado por el proveedor.",
                }
            ]
        }
    )

    monto_autorizado: Optional[Decimal] = Field(
        default=None,
        gt=0,
        description="Monto final autorizado; si se omite se autoriza el monto solicitado",
    )
    comentario: Optional[str] = Field(default=None, description="Comentario opcional de la aprobación")


class RechazoCreate(DecisionBase):
    model_config = ConfigDict(
        json_schema_extra={
            "examples": [
                {
                    "autorizador_id": "DIR-CARLOS",
                    "autorizador_nombre": "Carlos Ruiz",
                    "rol_autorizador": "Dirección",
                    "comentario": "El gasto no corresponde a la etapa actual de la obra.",
                }
            ]
        }
    )

    # validate_default para que la ausencia del comentario también dé el mensaje de negocio
    comentario: Optional[str] = Field(
        default=None,
        validate_default=True,
        description="Justificación obligatoria del rechazo",
    )

    @field_validator("comentario")
    @classmethod
    def validar_comentario_obligatorio(cls, v: Optional[str]) -> str:
        if not v or len(v) < LONGITUD_MINIMA_COMENTARIO_RECHAZO:
            raise ValueError("Es obligatorio ingresar un comentario que justifique el rechazo.")
        return v


class Autorizacion(BaseModel):
    """Registro inmutable de quién decidió, cuándo, por cuánto y por qué."""

    decision: DecisionAutorizacion
    autorizador_id: str
    autorizador_nombre: str
    rol_autorizador: RolAutorizador
    monto_autorizado: Optional[Decimal] = Field(default=None, description="Monto final; vacío si se rechazó")
    comentario: Optional[str] = Field(default=None)
    fecha_decision: datetime = Field(default_factory=_ahora_utc)


class BloqueoAdeudo(BaseModel):
    """Comprobaciones vencidas del solicitante que impiden autorizar un fondo nuevo (RF04/HU04).

    Se calcula al consultar la solicitud; no se guarda en la base de datos.
    """

    bloqueada: bool = Field(..., description="True si el solicitante tiene comprobaciones vencidas")
    comprobaciones_vencidas: int = Field(default=0, description="Solicitudes aprobadas sin comprobar fuera del límite")
    monto_por_comprobar: Decimal = Field(default=Decimal("0.00"), description="Suma pendiente de comprobar de las vencidas")
    folios_vencidos: List[str] = Field(default_factory=list, description="Folios de las solicitudes vencidas")
    limite_dias: int = Field(..., description="Días máximos para comprobar un fondo aprobado")
    mensaje: Optional[str] = Field(default=None, description="Aviso para el residente y el autorizador")


class SolicitudFondo(SolicitudFondoBase):
    id: UUID = Field(default_factory=uuid4, description="UUID identificador del registro")
    folio: str = Field(..., description="Folio único y legible generado automáticamente")
    firma_digital_direccion: Optional[str] = Field(default=None, description="Firma digital proporcionada para montos altos")
    nivel_autorizacion: str = Field(..., description="Nivel asignado según el monto: Administración o Dirección")
    estado: EstadoSolicitud = Field(default=EstadoSolicitud.PENDIENTE, description="Estado de la solicitud")
    autorizacion: Optional[Autorizacion] = Field(default=None, description="Decisión de aprobación o rechazo (RF05)")
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")
    deleted_at: Optional[datetime] = Field(default=None, description="Fecha de borrado lógico")
    created_at: datetime = Field(default_factory=_ahora_utc, description="Fecha de creación")
    updated_at: datetime = Field(default_factory=_ahora_utc, description="Fecha de última actualización")
    bloqueo: Optional[BloqueoAdeudo] = Field(
        default=None,
        description="Bloqueo por comprobaciones vencidas (RF04); solo se calcula en solicitudes pendientes",
    )


class SolicitudFondoResponse(BaseModel):
    solicitud: SolicitudFondo
    notificacion_enviada: NotificacionNivelAutorizacion
