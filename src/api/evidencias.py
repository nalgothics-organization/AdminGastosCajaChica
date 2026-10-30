"""Endpoints para la fotografía de evidencia de una solicitud de fondo (RF01/HU01).

La foto muestra lo que falta o se dañó; se guarda aparte de los comprobantes y la solicitud
solo conserva la URL que devuelve la subida.
"""

import re
from uuid import uuid4

from fastapi import APIRouter, File, HTTPException, UploadFile, status
from fastapi.responses import FileResponse
from pydantic import BaseModel
from src.services.comprobante_service import comprobante_service

router = APIRouter()

NOMBRE_VALIDO = re.compile(r"^[0-9a-f-]{36}\.(jpg|png|webp)$")


class EvidenciaSubida(BaseModel):
    evidencia_url: str


def _carpeta():
    return comprobante_service.uploads_dir / "evidencias"


@router.post(
    "/solicitudes/evidencia",
    response_model=EvidenciaSubida,
    status_code=status.HTTP_201_CREATED,
    summary="Subir fotografía de evidencia de la necesidad",
    description="Guarda la foto (JPEG, PNG o WEBP) y devuelve la URL para usarla como evidencia_url.",
    responses={status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "La imagen no es válida o no es legible."}},
)
async def subir_evidencia(imagen: UploadFile = File(..., description="Fotografía de la evidencia")):
    contenido = await imagen.read()
    try:
        extension = comprobante_service.validar_imagen(contenido, imagen.content_type or "")
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))
    nombre = f"{uuid4()}{extension}"
    _carpeta().mkdir(parents=True, exist_ok=True)
    (_carpeta() / nombre).write_bytes(contenido)
    return EvidenciaSubida(evidencia_url=f"/api/evidencias/{nombre}")


@router.get(
    "/evidencias/{nombre}",
    summary="Ver fotografía de evidencia",
    responses={status.HTTP_404_NOT_FOUND: {"description": "La fotografía no existe."}},
)
def ver_evidencia(nombre: str):
    ruta = _carpeta() / nombre
    if not NOMBRE_VALIDO.match(nombre) or not ruta.is_file():
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="La fotografía no existe.")
    return FileResponse(ruta)
