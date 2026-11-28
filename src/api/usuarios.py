"""Endpoints REST de usuarios: registro, inicio de sesión y administración básica (RF15/HU20).

El inicio de sesión del prototipo solo verifica la contraseña y devuelve los datos públicos del
usuario; las pantallas los guardan en el navegador para mostrar los apartados de su rol.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

from typing import List, Optional
from uuid import UUID

from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field

from src.models.usuario import RolUsuario, UsuarioCreate, UsuarioPublico
from src.services.usuario_service import (
    UsuarioDuplicadoError,
    UsuarioNoEncontradoError,
    usuario_service,
)

router = APIRouter()


class InicioSesion(BaseModel):
    usuario: str = Field(..., min_length=1, description="Nombre de usuario (no distingue mayúsculas)")
    contrasena: str = Field(..., min_length=1, description="Contraseña")


class CambioContrasena(BaseModel):
    actual: str = Field(..., min_length=1, description="Contraseña actual")
    nueva: str = Field(..., min_length=1, description="Contraseña nueva (mínimo 8 caracteres)")


def _no_encontrado(detalle: str) -> HTTPException:
    return HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=detalle)


@router.post(
    "/usuarios",
    response_model=UsuarioPublico,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar un usuario",
    description="Crea una cuenta con rol; el residente de obra debe indicar una obra activa. Nunca devuelve la contraseña.",
)
def registrar_usuario(data: UsuarioCreate):
    try:
        return usuario_service.crear(data).publico()
    except UsuarioDuplicadoError as e:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail=str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.post(
    "/sesion",
    response_model=UsuarioPublico,
    summary="Iniciar sesión",
    description="Verifica usuario y contraseña; responde 401 con el mismo mensaje si el usuario no existe o la contraseña no coincide.",
)
def iniciar_sesion(data: InicioSesion):
    usuario = usuario_service.autenticar(data.usuario, data.contrasena)
    if not usuario:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Usuario o contraseña incorrectos.")
    return usuario.publico()


@router.get(
    "/usuarios",
    response_model=List[UsuarioPublico],
    summary="Listar usuarios activos",
    description="Filtra opcionalmente por rol.",
)
def listar_usuarios(rol: Optional[RolUsuario] = None):
    usuarios = sorted(usuario_service.listar(rol), key=lambda u: u.usuario)
    return [u.publico() for u in usuarios]


@router.get(
    "/usuarios/{nombre_usuario}",
    response_model=UsuarioPublico,
    summary="Obtener un usuario activo por su nombre de usuario",
)
def obtener_usuario(nombre_usuario: str):
    usuario = usuario_service.obtener_por_usuario(nombre_usuario)
    if not usuario:
        raise _no_encontrado(f"El usuario {nombre_usuario} no existe o está dado de baja.")
    return usuario.publico()


@router.put(
    "/usuarios/{usuario_id}/contrasena",
    response_model=UsuarioPublico,
    summary="Cambiar la contraseña",
    description="Exige la contraseña actual.",
)
def cambiar_contrasena(usuario_id: UUID, data: CambioContrasena):
    try:
        return usuario_service.cambiar_contrasena(usuario_id, data.actual, data.nueva).publico()
    except UsuarioNoEncontradoError as e:
        raise _no_encontrado(str(e))
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e))


@router.delete(
    "/usuarios/{usuario_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Dar de baja un usuario (soft delete)",
    description="El registro se conserva para la auditoría de solicitudes y autorizaciones.",
)
def dar_de_baja(usuario_id: UUID):
    if not usuario_service.desactivar(usuario_id):
        raise _no_encontrado(f"Usuario con ID {usuario_id} no encontrado.")
    return None
