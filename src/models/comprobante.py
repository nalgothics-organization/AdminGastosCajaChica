"""Modelos y esquemas de datos para RF07/HU07 (comprobación) y RNF01/HU16 (captura rápida).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from datetime import date, datetime, timezone
from decimal import Decimal
from enum import Enum
from typing import List, Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, computed_field, field_validator, model_validator

from src.models.solicitud import EtapaConstruccion


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


# Partidas cuyo concepto se cobra por tiempo: exigen horas de maquinaria o de trabajo (RF07)
PARTIDAS_CON_HORAS = {"renta de maquinaria", "mano de obra"}


def partida_requiere_horas(partida_categoria: str) -> bool:
    return partida_categoria.strip().lower() in PARTIDAS_CON_HORAS


class TipoComprobante(str, Enum):
    FACTURA = "factura"
    TICKET = "ticket"
    NOTA_SIMPLE = "nota_simple"


class UnidadHoras(str, Enum):
    MAQUINARIA = "maquinaria"
    TRABAJO = "trabajo"


class EstadoComprobante(str, Enum):
    BORRADOR = "Borrador"
    COMPROBADO = "Comprobado"
    REVISION_CONTABILIDAD = "Revisión contabilidad"


class TipoRegistro(str, Enum):
    ORIGINAL = "original"
    AJUSTE = "ajuste"
    REVERSO = "reverso"


ESTADOS_CERRADOS = {EstadoComprobante.COMPROBADO, EstadoComprobante.REVISION_CONTABILIDAD}


class ComprobanteDatos(BaseModel):
    """Datos del formulario de comprobación (fase 2, se capturan después de la foto)."""

    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "tipo": "nota_simple",
                    "monto_comprobado": "3200.00",
                    "fecha_gasto": "2026-10-28",
                    "proveedor": "Maquinaria El Güero",
                    "concepto": "Renta de retroexcavadora",
                    "horas": "4.5",
                    "unidad_horas": "maquinaria",
                    "solicitud_id": None,
                }
            ]
        },
    )

    tipo: TipoComprobante = Field(..., description="Tipo de comprobante")
    monto_comprobado: Decimal = Field(..., gt=0, description="Monto pagado según el comprobante")
    fecha_gasto: date = Field(..., description="Fecha en que se realizó el gasto")
    proveedor: str = Field(..., min_length=2, description="Proveedor o persona que recibió el pago")
    concepto: str = Field(..., min_length=3, description="Concepto del gasto")
    horas: Optional[Decimal] = Field(default=None, gt=0, description="Horas de maquinaria o de trabajo, si aplica")
    unidad_horas: Optional[UnidadHoras] = Field(default=None, description="Indica si las horas son de maquinaria o de trabajo")
    solicitud_id: Optional[UUID] = Field(
        default=None,
        description="Solicitud a la que se vincula; solo se usa si la captura rápida no encontró una",
    )
    # Gasto por cuenta del residente: sin solicitud previa la clasificación (RF02) se captura aquí
    obra_id: Optional[str] = Field(default=None, description="Obra del gasto; obligatoria si no hay solicitud")
    etapa_construccion: Optional[EtapaConstruccion] = Field(
        default=None, description="Etapa del gasto; obligatoria si no hay solicitud"
    )
    partida_categoria: Optional[str] = Field(
        default=None, description="Partida del gasto; obligatoria si no hay solicitud"
    )

    @field_validator("fecha_gasto")
    @classmethod
    def validar_fecha_no_futura(cls, v: date) -> date:
        if v > date.today():
            raise ValueError("La fecha del gasto no puede ser futura.")
        return v

    @model_validator(mode="after")
    def validar_horas_completas(self) -> "ComprobanteDatos":
        # Las horas y su unidad viajan juntas; si aplican o no lo decide el servicio según la partida
        if (self.horas is None) != (self.unidad_horas is None):
            raise ValueError("Las horas y su unidad (maquinaria o trabajo) deben indicarse juntas.")
        return self


class AjusteCreate(BaseModel):
    """Corrección de un comprobante cerrado: nunca se edita el original (AGENTS.md §8)."""

    model_config = ConfigDict(str_strip_whitespace=True)

    tipo_registro: TipoRegistro = Field(..., description="ajuste (datos corregidos) o reverso (anula el original)")
    motivo: str = Field(..., min_length=5, description="Justificación de la corrección")
    datos: Optional[ComprobanteDatos] = Field(default=None, description="Datos corregidos; obligatorio para un ajuste")

    @model_validator(mode="after")
    def validar_tipo_registro(self) -> "AjusteCreate":
        if self.tipo_registro == TipoRegistro.ORIGINAL:
            raise ValueError("Una corrección debe ser de tipo ajuste o reverso.")
        if self.tipo_registro == TipoRegistro.AJUSTE and self.datos is None:
            raise ValueError("Un ajuste requiere los datos corregidos.")
        if self.tipo_registro == TipoRegistro.REVERSO and self.datos is not None:
            raise ValueError("Un reverso no lleva datos nuevos; anula el comprobante original.")
        return self


class LecturaComprobante(BaseModel):
    """Lo que el OCR alcanzó a distinguir en la foto (RF11/HU11).

    Cada dato que no se reconoce queda en None y aparece en `faltantes`: el residente lo completa a mano.
    No sustituye a `datos`, que solo existe cuando el residente confirma el formulario completo.
    """

    tipo: Optional[TipoComprobante] = Field(default=None, description="factura o ticket, si se reconoce")
    monto_comprobado: Optional[Decimal] = Field(default=None, description="Total pagado")
    fecha_gasto: Optional[date] = Field(default=None, description="Fecha impresa en el comprobante")
    proveedor: Optional[str] = Field(default=None, description="Nombre del comercio")
    renglones: List[str] = Field(default_factory=list, description="Texto leído de la foto, renglón por renglón")
    confianza: Optional[float] = Field(default=None, description="Confianza media del OCR, de 0 a 1")

    @computed_field(description="Datos que el OCR no pudo reconocer y quedan por completar")
    @property
    def faltantes(self) -> List[str]:
        campos = ("tipo", "monto_comprobado", "fecha_gasto", "proveedor")
        return [campo for campo in campos if getattr(self, campo) is None]


class Comprobante(BaseModel):
    id: UUID = Field(default_factory=uuid4, description="UUID identificador del registro")
    solicitante_id: str = Field(..., description="Residente que capturó el comprobante")
    solicitud_id: Optional[UUID] = Field(default=None, description="Solicitud de fondo vinculada")
    requiere_horas: Optional[bool] = Field(
        default=None,
        description="Si la partida de la solicitud exige horas; None mientras no haya solicitud vinculada",
    )
    obra_id: Optional[str] = Field(default=None, description="Obra a la que se carga el gasto (RF02)")
    etapa_construccion: Optional[EtapaConstruccion] = Field(default=None, description="Etapa del gasto (RF02)")
    partida_categoria: Optional[str] = Field(default=None, description="Partida del gasto (RF02)")
    imagen_ruta: str = Field(..., description="Ruta de la imagen almacenada")
    estado: EstadoComprobante = Field(default=EstadoComprobante.BORRADOR)
    tipo_registro: TipoRegistro = Field(default=TipoRegistro.ORIGINAL)
    comprobante_origen_id: Optional[UUID] = Field(default=None, description="UUID del comprobante corregido")
    motivo_correccion: Optional[str] = Field(default=None)
    datos: Optional[ComprobanteDatos] = Field(default=None, description="Datos del formulario de comprobación")
    lectura: Optional[LecturaComprobante] = Field(
        default=None, description="Datos que el OCR leyó de la foto; se confirman o completan en el formulario"
    )
    cierre_automatico: Optional[bool] = Field(
        default=None,
        description="True si el comprobante se cerró solo porque la lectura de la foto salió completa (RF08)",
    )
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")
    deleted_at: Optional[datetime] = Field(default=None, description="Fecha de borrado lógico")
    created_at: datetime = Field(default_factory=_ahora_utc)
    updated_at: datetime = Field(default_factory=_ahora_utc)
