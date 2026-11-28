"""Servicio de usuarios: alta, consulta, autenticación básica y baja lógica.

Los demás servicios lo usan para comprobar que quien solicita, comprueba o autoriza existe,
está activo y tiene el rol que la acción exige (base de RF15/HU20).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import hmac
from datetime import datetime, timezone
from typing import Iterable, List, Optional
from uuid import UUID

from src.models.usuario import LONGITUD_MINIMA_CONTRASENA, RolUsuario, Usuario, UsuarioCreate, normalizar_usuario
from src.repositories import UsuarioRepositorio
from src.services.obra_service import ObraService, obra_service as obra_service_default


class UsuarioNoEncontradoError(LookupError):
    """El usuario no existe o fue dado de baja."""


class UsuarioDuplicadoError(ValueError):
    """Ya hay un usuario con ese nombre de usuario o ese correo."""


class RolNoPermitidoError(PermissionError):
    """El rol del usuario no permite la acción solicitada."""


class UsuarioService:
    def __init__(self, obra_service: Optional[ObraService] = None):
        self._db = UsuarioRepositorio()
        self._obra_service = obra_service or obra_service_default

    def crear(self, data: UsuarioCreate) -> Usuario:
        """Da de alta un usuario; el usuario y el correo no se repiten ni con usuarios dados de baja."""
        if self._db.por_usuario(data.usuario):
            raise UsuarioDuplicadoError(f"El usuario {data.usuario} ya existe.")
        if self._db.por_email(data.email):
            raise UsuarioDuplicadoError(f"Ya hay un usuario con el correo {data.email}.")
        if data.obra_id:
            data = data.model_copy(update={"obra_id": self._obra_service.obtener_obra_activa(data.obra_id).id})

        usuario = Usuario(**data.model_dump(exclude={"contrasena"}), contrasena=data.contrasena)
        return self._db.guardar(usuario)

    def obtener_por_id(self, usuario_id: UUID) -> Optional[Usuario]:
        usuario = self._db.get(usuario_id)
        return usuario if usuario and usuario.activo else None

    def obtener_por_usuario(self, nombre_usuario: str) -> Optional[Usuario]:
        usuario = self._db.por_usuario(normalizar_usuario(nombre_usuario))
        return usuario if usuario and usuario.activo else None

    def listar(self, rol: Optional[RolUsuario] = None) -> List[Usuario]:
        return [u for u in self._db.values() if u.activo and (rol is None or u.rol == rol)]

    def autenticar(self, nombre_usuario: str, contrasena: str) -> Optional[Usuario]:
        """Devuelve el usuario si la contraseña coincide; None si no existe, está inactivo o no coincide."""
        usuario = self.obtener_por_usuario(nombre_usuario)
        if not usuario or not contrasena:
            return None
        # compare_digest tarda lo mismo acierte o no, para no dar pistas de la contraseña
        if not hmac.compare_digest(usuario.contrasena.encode("utf-8"), contrasena.encode("utf-8")):
            return None
        return usuario

    def cambiar_contrasena(self, usuario_id: UUID, actual: str, nueva: str) -> Usuario:
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            raise UsuarioNoEncontradoError(f"Usuario con ID {usuario_id} no encontrado.")
        if not self.autenticar(usuario.usuario, actual):
            raise ValueError("La contraseña actual no es correcta.")
        if len(nueva or "") < LONGITUD_MINIMA_CONTRASENA:
            raise ValueError(f"La contraseña nueva debe tener al menos {LONGITUD_MINIMA_CONTRASENA} caracteres.")
        usuario.contrasena = nueva
        usuario.updated_at = datetime.now(timezone.utc)
        return self._db.guardar(usuario)

    def exigir(self, nombre_usuario: str, roles: Iterable[RolUsuario], accion: str) -> Usuario:
        """Devuelve el usuario activo si su rol permite `accion`; si no, lanza el error correspondiente."""
        usuario = self.obtener_por_usuario(nombre_usuario)
        if not usuario:
            raise UsuarioNoEncontradoError(
                f"El usuario {normalizar_usuario(nombre_usuario)} no existe o está dado de baja."
            )
        roles = tuple(roles)
        if usuario.rol not in roles:
            permitidos = " o ".join(r.value for r in roles)
            raise RolNoPermitidoError(
                f"{usuario.nombre} tiene el rol {usuario.rol.value} y no puede {accion}; se requiere {permitidos}."
            )
        return usuario

    def desactivar(self, usuario_id: UUID) -> bool:
        """Baja lógica: el registro se conserva para la auditoría de solicitudes y autorizaciones."""
        usuario = self.obtener_por_id(usuario_id)
        if not usuario:
            return False
        usuario.activo = False
        usuario.deleted_at = datetime.now(timezone.utc)
        usuario.updated_at = usuario.deleted_at
        self._db.guardar(usuario)
        return True


usuario_service = UsuarioService()
