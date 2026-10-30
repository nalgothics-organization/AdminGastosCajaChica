"""Catálogo de obras existentes para elegirlas en los formularios.

El alta de obras y su presupuesto es otro módulo que aún no está contemplado; mientras tanto
este catálogo simulado sirve las obras ya registradas. Reglas de codificación: UTF-8, LF, 4 espacios.
"""

from decimal import Decimal
from typing import List

from fastapi import APIRouter
from pydantic import BaseModel, Field

router = APIRouter()


class ObraCatalogo(BaseModel):
    id: str = Field(..., description="Identificador de la obra, el que usan solicitudes y comprobantes")
    nombre: str = Field(..., description="Nombre de la obra")
    presupuesto: Decimal = Field(..., description="Presupuesto total asignado a la obra")


# Datos simulados: deben coincidir con las obras de src/seed.py
OBRAS = [
    ObraCatalogo(id="OBRA-NORTE-01", nombre="Torre Residencial Cimas Norte", presupuesto=Decimal("2500000.00")),
    ObraCatalogo(id="OBRA-SUR-02", nombre="Plaza Comercial Cimas Sur", presupuesto=Decimal("1800000.00")),
    ObraCatalogo(id="OBRA-PONIENTE-03", nombre="Conjunto Habitacional Poniente", presupuesto=Decimal("3200000.00")),
]


@router.get(
    "/catalogo/obras",
    response_model=List[ObraCatalogo],
    summary="Listar obras existentes",
    description="Obras ya registradas con su presupuesto, para elegirlas en un menú desplegable.",
)
def listar_obras():
    return OBRAS
