"""Modelos de usuario y rol (base de RF15/HU20).

Cada persona que usa el sistema tiene un usuario con un rol: residente de obra, administración,
dirección o contabilidad. El campo `usuario` es el identificador legible que guardan las solicitudes
(solicitante) y las autorizaciones (autorizador).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import re
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import UUID, uuid4

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# Letras, números, punto, guion y guion bajo; se guarda en mayúsculas (RESIDENTE-PAU, ADMIN-LAURA)
FORMATO_USUARIO = re.compile(r"^[A-Z0-9][A-Z0-9._-]{2,39}$")
FORMATO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
LONGITUD_MINIMA_CONTRASENA = 8


def _ahora_utc() -> datetime:
    return datetime.now(timezone.utc)


class RolUsuario(str, Enum):
    RESIDENTE = "Residente de obra"
    ADMINISTRACION = "Administración"
    DIRECCION = "Dirección"
    CONTABILIDAD = "Contabilidad"


def normalizar_usuario(valor: str) -> str:
    return (valor or "").strip().upper()


class UsuarioBase(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    usuario: str = Field(..., description="Nombre de usuario para iniciar sesión, único (se guarda en mayúsculas)")
    nombre: str = Field(..., min_length=3, max_length=120, description="Nombre completo de la persona")
    email: str = Field(..., max_length=120, description="Correo electrónico, único")
    rol: RolUsuario = Field(..., description="Rol que define los apartados y acciones permitidas")
    obra_id: Optional[str] = Field(
        default=None, description="Obra asignada; obligatoria para el residente de obra"
    )

    @field_validator("usuario")
    @classmethod
    def validar_usuario(cls, v: str) -> str:
        v = normalizar_usuario(v)
        if not FORMATO_USUARIO.match(v):
            raise ValueError(
                "El usuario debe tener de 3 a 40 caracteres: letras, números, punto, guion o guion bajo."
            )
        return v

    @field_validator("email")
    @classmethod
    def validar_email(cls, v: str) -> str:
        v = v.strip().lower()
        if not FORMATO_EMAIL.match(v):
            raise ValueError("El correo electrónico no es válido.")
        return v

    @field_validator("obra_id")
    @classmethod
    def limpiar_obra(cls, v: Optional[str]) -> Optional[str]:
        return v.strip() or None if v else None

    @model_validator(mode="after")
    def validar_obra_del_residente(self) -> "UsuarioBase":
        if self.rol == RolUsuario.RESIDENTE and not self.obra_id:
            raise ValueError("El residente de obra debe tener una obra asignada.")
        return self


class UsuarioCreate(UsuarioBase):
    model_config = ConfigDict(
        str_strip_whitespace=True,
        json_schema_extra={
            "examples": [
                {
                    "usuario": "RESIDENTE-PAU",
                    "nombre": "Paula Rivas",
                    "email": "paula.rivas@cimas.example",
                    "rol": "Residente de obra",
                    "obra_id": "OBRA-NORTE-01",
                    "contrasena": "una-contrasena-local",
                }
            ]
        },
    )

    contrasena: str = Field(
        ...,
        min_length=LONGITUD_MINIMA_CONTRASENA,
        max_length=128,
        description="Contraseña para iniciar sesión",
    )


class UsuarioPublico(UsuarioBase):
    """Datos del usuario que se pueden mostrar; nunca incluye la contraseña."""

    id: UUID = Field(default_factory=uuid4, description="UUID identificador del registro")
    activo: bool = Field(default=True, description="Indicador para borrado lógico (soft delete)")
    deleted_at: Optional[datetime] = Field(default=None, description="Fecha de baja lógica")
    created_at: datetime = Field(default_factory=_ahora_utc)
    updated_at: datetime = Field(default_factory=_ahora_utc)


class Usuario(UsuarioPublico):
    # Contraseña en texto plano por decisión del equipo para el prototipo; repr=False la oculta en logs
    contrasena: str = Field(..., repr=False, exclude=True, description="Contraseña (no se serializa)")

    def publico(self) -> UsuarioPublico:
        return UsuarioPublico(**self.model_dump())
