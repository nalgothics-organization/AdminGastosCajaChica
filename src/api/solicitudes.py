"""Endpoints REST para el módulo de Solicitudes de Fondo (RF01, HU01).
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.models.solicitud import SolicitudFondo, SolicitudFondoCreate, SolicitudFondoResponse
from src.services.solicitud_service import solicitud_service

router = APIRouter()


class ErrorResponse(BaseModel):
    detail: str


RESPUESTA_404 = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La solicitud no existe o fue eliminada lógicamente.",
    },
}


@router.post(
    "/solicitudes",
    response_model=SolicitudFondoResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar solicitud de fondo de caja chica",
    description=(
        "Registra una solicitud de fondo (RF01/HU01). Requiere evidencia de la necesidad, "
        "genera un folio único y notifica al nivel de autorización correspondiente: "
        "Administración para montos de hasta 5,000 MXN y Dirección para montos mayores, "
        "en cuyo caso la firma digital de Dirección es obligatoria."
    ),
    response_description="Solicitud registrada y notificación emitida.",
    responses={
        status.HTTP_422_UNPROCESSABLE_ENTITY: {
            "description": "Datos inválidos: falta evidencia, montos no positivos o falta la firma de Dirección.",
        },
    },
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
    description="Devuelve todas las solicitudes que no han sido eliminadas lógicamente.",
    response_description="Lista de solicitudes activas.",
)
def listar_solicitudes():
    return solicitud_service.listar_solicitudes_activas()


@router.get(
    "/solicitudes/{solicitud_id}",
    response_model=SolicitudFondo,
    summary="Obtener solicitud por ID",
    description="Obtiene una solicitud activa a partir de su UUID.",
    response_description="Solicitud encontrada.",
    responses=RESPUESTA_404,
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
    description=(
        "Marca la solicitud como inactiva y registra la fecha de borrado. "
        "Nunca se elimina físicamente el registro para conservar la auditoría."
    ),
    response_description="Solicitud eliminada lógicamente.",
    responses=RESPUESTA_404,
)
def eliminar_solicitud(solicitud_id: UUID):
    exito = solicitud_service.soft_delete(solicitud_id)
    if not exito:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Solicitud con ID {solicitud_id} no encontrada o ya inactiva.",
        )
    return None
