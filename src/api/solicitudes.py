"""Endpoints REST para el módulo de Solicitudes de Fondo (RF01/HU01, RF05/HU05, RF06/HU06).
"""

from typing import List
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel
from src.models.solicitud import (
    AprobacionCreate,
    EntregaCreate,
    RechazoCreate,
    SolicitudFondo,
    SolicitudFondoCreate,
    SolicitudFondoResponse,
)
from src.services.solicitud_service import (
    AutorizadorNoPermitidoError,
    EntregaNoPermitidaError,
    SolicitudBloqueadaError,
    SolicitudNoEncontradaError,
    SolicitudNoPendienteError,
    solicitud_service,
)

router = APIRouter()


class ErrorResponse(BaseModel):
    detail: str


RESPUESTA_404 = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "La solicitud no existe o fue eliminada lógicamente.",
    },
}

RESPUESTAS_DECISION = {
    **RESPUESTA_404,
    status.HTTP_403_FORBIDDEN: {
        "model": ErrorResponse,
        "description": "El rol del autorizador no alcanza el nivel que exige el monto de la solicitud.",
    },
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "La solicitud ya fue aprobada o rechazada; no puede decidirse de nuevo.",
    },
    status.HTTP_423_LOCKED: {
        "model": ErrorResponse,
        "description": "El solicitante tiene comprobaciones vencidas; no se autoriza un fondo nuevo (RF04).",
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Datos inválidos: rol desconocido, monto fuera de rango o falta el comentario del rechazo.",
    },
}


RESPUESTAS_ENTREGA = {
    **RESPUESTA_404,
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "La solicitud no está aprobada o ya tiene su entrega registrada.",
    },
    status.HTTP_423_LOCKED: {
        "model": ErrorResponse,
        "description": "El solicitante tiene comprobaciones vencidas; no se le entrega un fondo nuevo (RF04).",
    },
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Datos inválidos: falta la referencia bancaria, la fecha es futura o anterior a la autorización.",
    },
}


def _ejecutar(operacion, *args):
    """Traduce las excepciones de negocio del servicio a respuestas HTTP."""
    try:
        return operacion(*args)
    except SolicitudNoEncontradaError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except AutorizadorNoPermitidoError as e:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(e))
    except (SolicitudNoPendienteError, EntregaNoPermitidaError) as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except SolicitudBloqueadaError as e:
        raise HTTPException(status_code=status.HTTP_423_LOCKED, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


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
    description=(
        "Devuelve todas las solicitudes que no han sido eliminadas lógicamente. Las pendientes incluyen "
        "`bloqueo`, que indica si el residente tiene comprobaciones vencidas y no puede recibir el fondo (RF04)."
    ),
    response_description="Lista de solicitudes activas.",
)
def listar_solicitudes():
    return solicitud_service.anotar_bloqueos(solicitud_service.listar_solicitudes_activas())


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
    return solicitud_service.anotar_bloqueos([solicitud])[0]


@router.post(
    "/solicitudes/{solicitud_id}/aprobar",
    response_model=SolicitudFondo,
    summary="Aprobar solicitud de fondo",
    description=(
        "Aprueba una solicitud pendiente (RF05/HU05) y registra quién autorizó, cuándo, "
        "el monto final autorizado y un comentario opcional. Si no se indica monto se autoriza "
        "el solicitado; nunca puede ser mayor. Administración decide montos de hasta 5,000 MXN "
        "y Dirección cualquier monto. Se rechaza con 423 si el residente tiene comprobaciones "
        "pendientes con más días que el límite configurado (RF04/HU04)."
    ),
    response_description="Solicitud aprobada con su registro de autorización.",
    responses=RESPUESTAS_DECISION,
)
def aprobar_solicitud(solicitud_id: UUID, data: AprobacionCreate):
    return _ejecutar(solicitud_service.aprobar_solicitud, solicitud_id, data)


@router.post(
    "/solicitudes/{solicitud_id}/rechazar",
    response_model=SolicitudFondo,
    summary="Rechazar solicitud de fondo",
    description=(
        "Rechaza una solicitud pendiente (RF05/HU05). El comentario que justifica la decisión "
        "es obligatorio y queda registrado junto con quién rechazó y cuándo."
    ),
    response_description="Solicitud rechazada con su registro de autorización.",
    responses=RESPUESTAS_DECISION,
)
def rechazar_solicitud(solicitud_id: UUID, data: RechazoCreate):
    return _ejecutar(solicitud_service.rechazar_solicitud, solicitud_id, data)


@router.post(
    "/solicitudes/{solicitud_id}/entrega",
    response_model=SolicitudFondo,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar la entrega del recurso",
    description=(
        "Registra cómo salió el dinero de una solicitud aprobada (RF06/HU06): forma de entrega (efectivo, "
        "transferencia o tarjeta), fecha, referencia bancaria y la persona que lo entregó. La referencia es "
        "obligatoria en transferencia y tarjeta; en efectivo basta con marcarlo. Cada solicitud se entrega una "
        "sola vez (409) y solo si está aprobada. Se rechaza con 423 si el residente tiene comprobaciones "
        "vencidas de fondos ya entregados (RF04/HU04). La solicitud devuelve el registro en `entrega`."
    ),
    response_description="Solicitud con su registro de entrega.",
    responses=RESPUESTAS_ENTREGA,
)
def registrar_entrega(solicitud_id: UUID, data: EntregaCreate):
    return _ejecutar(solicitud_service.registrar_entrega, solicitud_id, data)


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
