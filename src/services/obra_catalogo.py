"""Obras existentes con su fondo de caja chica.

El alta de obras y de su fondo es otro módulo que aún no está contemplado; mientras tanto este
catálogo simulado sirve las obras ya registradas (deben coincidir con las de src/seed.py).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from decimal import Decimal
from typing import List

from pydantic import BaseModel, Field


class ObraCatalogo(BaseModel):
    id: str = Field(..., description="Identificador de la obra, el que usan solicitudes y comprobantes")
    nombre: str = Field(..., description="Nombre de la obra")
    presupuesto_caja_chica: Decimal = Field(..., description="Fondo de caja chica asignado a la obra")


OBRAS: List[ObraCatalogo] = [
    ObraCatalogo(id="OBRA-NORTE-01", nombre="Torre Residencial Cimas Norte", presupuesto_caja_chica=Decimal("20000.00")),
    ObraCatalogo(id="OBRA-SUR-02", nombre="Plaza Comercial Cimas Sur", presupuesto_caja_chica=Decimal("50000.00")),
    ObraCatalogo(id="OBRA-PONIENTE-03", nombre="Conjunto Habitacional Poniente", presupuesto_caja_chica=Decimal("30000.00")),
]
