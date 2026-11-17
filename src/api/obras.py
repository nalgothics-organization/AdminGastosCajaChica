"""Endpoints REST para el catálogo de Obras y Partidas Presupuestales (RF02, HU02).
"""

from typing import List

from fastapi import APIRouter, HTTPException, status
from src.models.obra import Obra, PartidaPresupuestal
from src.services.obra_service import obra_service

router = APIRouter()

@router.get(
    "/obras",
    response_model=List[Obra],
    summary="Listar obras activas",
)
def listar_obras():
    return obra_service.listar_obras_activas()


@router.get(
    "/obras/{obra_id}/partidas",
    response_model=List[PartidaPresupuestal],
    summary="Listar partidas presupuestales de una obra activa",
)
def listar_partidas(obra_id: str):
    try:
        return obra_service.listar_partidas(obra_id)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        )


@router.post(
    "/obras",
    response_model=Obra,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar una obra con sus partidas presupuestales",
)
def registrar_obra(obra: Obra):
    try:
        return obra_service.registrar_obra(obra)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(e),
        )


@router.delete(
    "/obras/{obra_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Borrar una obra por su id, soft delete",
)
def borrar_obra(obra_id: str):
    deleted = obra_service.soft_delete(obra_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Obra con id {obra_id} no fue encontrada o está inactiva.",
        )
    return None
