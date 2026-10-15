"""Modelos de datos para el catálogo de Obras y Partidas Presupuestales (RF02/HU02).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field, field_validator

# Nombres de partida que se consideran gastos genéricos y no se permiten (RF02)
PARTIDAS_GENERICAS_PROHIBIDAS = {
    "varios",
    "general",
    "generico",
    "genérico",
    "otros",
    "otro",
    "misc",
    "miscelaneo",
    "misceláneo",
    "miscelaneos",
    "misceláneos",
    "sin partida",
    "sin categoria",
    "sin categoría",
    "n/a",
    "na",
}


def normalizar_texto(valor: str) -> str:
    """Normaliza un texto para comparaciones insensibles a mayúsculas y espacios."""
    return " ".join(valor.split()).lower()


def es_partida_generica(nombre: str) -> bool:
    return normalizar_texto(nombre) in PARTIDAS_GENERICAS_PROHIBIDAS


class EstadoObra(str, Enum):
    ACTIVA = "Activa"
    SUSPENDIDA = "Suspendida"
    CERRADA = "Cerrada"


class PartidaPresupuestal(BaseModel):
    clave: str = Field(..., min_length=1, description="Clave de la partida presupuestal")
    nombre: str = Field(..., min_length=1, description="Nombre de la partida presupuestal")
    monto_presupuestado: Decimal = Field(default=Decimal("0"), ge=0, description="Monto cotizado para la partida")
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")

    @field_validator("clave", "nombre")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("La clave y el nombre de la partida son obligatorios.")
        return v.strip()

    @field_validator("nombre")
    @classmethod
    def validar_no_generica(cls, v: str) -> str:
        if es_partida_generica(v):
            raise ValueError("No se permiten partidas genéricas en el presupuesto de la obra.")
        return v


class Obra(BaseModel):
    id: str = Field(..., min_length=1, description="Identificador de la obra")
    nombre: str = Field(..., min_length=1, description="Nombre de la obra")
    estado: EstadoObra = Field(default=EstadoObra.ACTIVA, description="Estado de la obra")
    partidas: List[PartidaPresupuestal] = Field(default_factory=list, description="Partidas presupuestales de la obra")
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")
    deleted_at: Optional[datetime] = Field(default=None, description="Fecha de borrado lógico")
    created_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de creación")
    updated_at: datetime = Field(default_factory=datetime.utcnow, description="Fecha de última actualización")

    @field_validator("id", "nombre")
    @classmethod
    def validar_no_vacio(cls, v: str) -> str:
        if not v or not v.strip():
            raise ValueError("El identificador y el nombre de la obra son obligatorios.")
        return v.strip()
