"""Endpoints REST de saldos por obra (RF10, HU10).
"""

from typing import List

from fastapi import APIRouter
from src.services.saldo_service import SaldoObra, saldo_service

router = APIRouter()


@router.get(
    "/saldos",
    response_model=List[SaldoObra],
    summary="Saldos por obra en tiempo real",
    description=(
        "Para cada obra devuelve su fondo de caja chica y lo disponible tras las aprobaciones, lo "
        "comprobado, lo que falta por comprobar, el gasto pagado sin solicitud (reembolso pendiente) y "
        "lo que espera autorización."
    ),
    response_description="Un renglón por obra con movimientos.",
)
def saldos_por_obra():
    return saldo_service.por_obra()
