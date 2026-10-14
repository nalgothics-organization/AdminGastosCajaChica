"""Endpoints REST para el módulo de Solicitudes de Fondo (RF01, HU01).
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from src.models.solicitud import SolicitudFondo, SolicitudFondoCreate, SolicitudFondoResponse
from src.services.solicitud_service import solicitud_service

router = APIRouter()


@router.post(
    "/solicitudes",
    response_model=SolicitudFondoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar solicitud de fondo de caja chica",
)
def registrar_solicitud(data: SolicitudFondoCreate):
    try:
        return solicitud_service.crear_solicitud(data)
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(e),
        )


@router.get(
    "/solicitudes",
    response_model=List[SolicitudFondo],
    summary="Listar solicitudes activas",
)
def listar_solicitudes():
    return solicitud_service.listar_solicitudes_activas()


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=SolicitudFondo,
    summary="Obtener solicitud por ID",
)
def obtener_solicitud(solicitud_id: UUID):
    solicitud = solicitud_service.obtener_por_id(solicitud_id)
    if not solicitud:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitud con ID {solicitud_id} no encontrada.",
        )
    return solicitud


@router.delete(
    "/solicitudes/{solicitud_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Eliminar lógicamente una solicitud (Soft delete)",
)
def eliminar_solicitud(solicitud_id: UUID):
    exito = solicitud_service.soft_delete(solicitud_id)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitud con ID {solicitud_id} no encontrada o ya inactiva.",
        )
    return None
