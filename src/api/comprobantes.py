"""Endpoints REST para la comprobación de gastos (RF07/HU07) y la captura rápida (RNF01/HU16).
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, File, Form, HTTPException, UploadFile, status
from fastapi.concurrency import run_in_threadpool
from pydantic import BaseModel
from src.models.comprobante import AjusteCreate, Comprobante, ComprobanteDatos, EstadoComprobante
from src.services.comprobante_service import (
    ComprobanteNoEncontradoError,
    EstadoNoEditableError,
    comprobante_service,
)

router = APIRouter()


class ErrorResponse(BaseModel):
    detail: str


RESPUESTA_404 = {
    status.HTTP_404_NOT_FOUND: {
        "model": ErrorResponse,
        "description": "El comprobante no existe o fue eliminado lógicamente.",
    },
}

RESPUESTA_409 = {
    status.HTTP_409_CONFLICT: {
        "model": ErrorResponse,
        "description": "El comprobante está cerrado; las correcciones se registran como ajuste o reverso.",
    },
}

RESPUESTA_422 = {
    status.HTTP_422_UNPROCESSABLE_ENTITY: {
        "description": "Datos inválidos o que no cumplen las reglas de la partida.",
    },
}


def _ejecutar(operacion, *args):
    """Traduce las excepciones de negocio del servicio a respuestas HTTP."""
    try:
        return operacion(*args)
    except ComprobanteNoEncontradoError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    except EstadoNoEditableError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/comprobantes/captura",
    response_model=Comprobante,
    status_code=status.HTTP_201_CREATED,
    summary="Captura rápida de comprobante (solo fotografía)",
    description=(
        "Guarda la fotografía del comprobante sin pedir ningún otro dato (RNF01/HU16). "
        "Si se indica la solicitud aprobada a la que corresponde el gasto, la foto queda vinculada a ella; "
        "si no, se elige al completar los datos. La foto se lee con OCR y se rechaza (422) si sale borrosa, "
        "oscura o no trae ningún monto, para que el residente la repita."
    ),
    response_description="Comprobante guardado en estado Borrador.",
    responses=RESPUESTA_422,
)
async def capturar_comprobante(
    solicitante_id: str = Form(..., description="Residente que captura"),
    imagen: UploadFile = File(..., description="Fotografía del comprobante (JPEG, PNG o WEBP)"),
    solicitud_id: Optional[UUID] = Form(default=None, description="Solicitud aprobada a la que corresponde el gasto"),
):
    contenido = await imagen.read()
    # El OCR tarda un par de segundos; corre en otro hilo para no detener las demás peticiones
    return await run_in_threadpool(
        _ejecutar,
        comprobante_service.capturar_rapido,
        solicitante_id,
        contenido,
        imagen.content_type or "",
        solicitud_id,
    )


@router.get(
    "/comprobantes",
    response_model=List[Comprobante],
    summary="Listar comprobantes activos",
    description="Filtra opcionalmente por residente y estado (p. ej. borradores por completar).",
    response_description="Lista de comprobantes activos.",
)
def listar_comprobantes(solicitante_id: Optional[str] = None, estado: Optional[EstadoComprobante] = None):
    return comprobante_service.listar(solicitante_id, estado)


@router.get(
    "/comprobantes/{comprobante_id}",
    response_model=Comprobante,
    summary="Obtener comprobante por ID",
    description="Incluye `requiere_horas` para que el formulario muestre u oculte las horas.",
    response_description="Comprobante encontrado.",
    responses=RESPUESTA_404,
)
def obtener_comprobante(comprobante_id: UUID):
    comprobante = comprobante_service.obtener_por_id(comprobante_id)
    if not comprobante:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Comprobante con ID {comprobante_id} no encontrado.",
        )
    return comprobante


@router.put(
    "/comprobantes/{comprobante_id}/datos",
    response_model=Comprobante,
    summary="Completar datos de la comprobación",
    description=(
        "Registra tipo, monto, fecha, proveedor y concepto (RF07/HU07). Las horas de maquinaria "
        "o de trabajo son obligatorias si la partida es Renta de Maquinaria o Mano de Obra, "
        "y deben ir vacías en las demás. Solo se permite mientras el comprobante esté en borrador."
    ),
    response_description="Comprobante con datos completos.",
    responses={**RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
def completar_datos(comprobante_id: UUID, datos: ComprobanteDatos):
    return _ejecutar(comprobante_service.completar_datos, comprobante_id, datos)


@router.post(
    "/comprobantes/{comprobante_id}/cerrar",
    response_model=Comprobante,
    summary="Cerrar la comprobación",
    description=(
        "Una factura queda como Comprobado; un ticket o nota simple pasa a revisión de contabilidad. "
        "Después de cerrar, el comprobante ya no se puede modificar."
    ),
    response_description="Comprobante cerrado.",
    responses={**RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
def cerrar_comprobante(comprobante_id: UUID):
    return _ejecutar(comprobante_service.cerrar, comprobante_id)


@router.post(
    "/comprobantes/{comprobante_id}/ajustes",
    response_model=Comprobante,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar ajuste o reverso de un comprobante cerrado",
    description=(
        "Crea un registro nuevo que referencia el UUID del comprobante original; "
        "el original nunca se modifica para conservar el historial contable."
    ),
    response_description="Registro de corrección creado.",
    responses={**RESPUESTA_404, **RESPUESTA_409, **RESPUESTA_422},
)
def registrar_ajuste(comprobante_id: UUID, correccion: AjusteCreate):
    return _ejecutar(comprobante_service.crear_ajuste, comprobante_id, correccion)


@router.delete(
    "/comprobantes/{comprobante_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Descartar un borrador (Soft delete)",
    description="Marca el borrador como inactivo. Los comprobantes cerrados no se pueden eliminar.",
    response_description="Borrador eliminado lógicamente.",
    responses={**RESPUESTA_404, **RESPUESTA_409},
)
def eliminar_comprobante(comprobante_id: UUID):
    _ejecutar(comprobante_service.soft_delete, comprobante_id)
    return None
