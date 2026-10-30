"""Catálogo de obras existentes para elegirlas en los formularios.

El disponible viene de los saldos por obra: fondo de caja chica menos lo autorizado en solicitudes
aprobadas. Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from decimal import Decimal
from typing import List

from fastapi import APIRouter
from pydantic import Field
from src.services.obra_catalogo import OBRAS, ObraCatalogo
from src.services.saldo_service import saldo_service

router = APIRouter()


class ObraConDisponible(ObraCatalogo):
    autorizado: Decimal = Field(..., description="Suma de los montos autorizados en solicitudes aprobadas")
    disponible_caja_chica: Decimal = Field(
        ..., description="Fondo de caja chica menos lo autorizado; baja con cada aprobación"
    )


@router.get(
    "/catalogo/obras",
    response_model=List[ObraConDisponible],
    summary="Listar obras existentes",
    description="Obras ya registradas con su fondo de caja chica y lo que queda disponible tras las aprobaciones.",
)
def listar_obras():
    saldos = {s.obra_id: s for s in saldo_service.por_obra()}
    return [
        ObraConDisponible(
            **obra.model_dump(),
            autorizado=saldos[obra.id].autorizado,
            disponible_caja_chica=saldos[obra.id].disponible_caja_chica,
        )
        for obra in OBRAS
    ]
