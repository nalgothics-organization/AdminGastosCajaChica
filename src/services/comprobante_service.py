"""Módulo de servicios de negocio para la comprobación de gastos.
Implementa:
- Captura rápida con solo la fotografía y vinculado automático a la solicitud (RNF01/HU16).
- Formulario de comprobación con horas de maquinaria o de trabajo condicionales (RF07/HU07).
- Inmutabilidad de comprobantes cerrados y correcciones por Ajuste/Reverso (AGENTS.md §8).
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Optional
from uuid import UUID, uuid4

from src.models.comprobante import (
    ESTADOS_CERRADOS,
    AjusteCreate,
    Comprobante,
    ComprobanteDatos,
    EstadoComprobante,
    TipoComprobante,
    TipoRegistro,
    partida_requiere_horas,
)
from src.models.solicitud import EstadoSolicitud
from src.services.solicitud_service import SolicitudFondoService, solicitud_service

# Firmas binarias de los formatos aceptados; no se confía solo en el content-type del cliente
FIRMAS_IMAGEN = {
    "image/jpeg": (b"\xff\xd8\xff", ".jpg"),
    "image/png": (b"\x89PNG\r\n\x1a\n", ".png"),
    "image/webp": (b"RIFF", ".webp"),
}

# Por debajo de este tamaño la foto difícilmente es legible
TAMANO_MINIMO_IMAGEN_BYTES = 20 * 1024


class ComprobanteNoEncontradoError(LookupError):
    pass


class EstadoNoEditableError(Exception):
    """El comprobante está cerrado o anulado y no admite cambios directos."""


class ComprobanteService:
    def __init__(
        self,
        solicitudes: SolicitudFondoService = solicitud_service,
        uploads_dir: Optional[str] = None,
    ):
        # Almacén en memoria simulado para persistencia
        self._db: Dict[UUID, Comprobante] = {}
        self._solicitudes = solicitudes
        self.uploads_dir = Path(uploads_dir or os.getenv("UPLOADS_DIR", "./uploads"))
        self.tamano_maximo_bytes = int(os.getenv("MAX_IMAGEN_MB", "10")) * 1024 * 1024

    def validar_imagen(self, contenido: bytes, content_type: str) -> str:
        """Valida formato y tamaño de la imagen; devuelve la extensión con la que se guarda."""
        formato = FIRMAS_IMAGEN.get(content_type)
        if not formato or not contenido.startswith(formato[0]):
            raise ValueError("La imagen debe ser JPEG, PNG o WEBP.")
        if content_type == "image/webp" and contenido[8:12] != b"WEBP":
            raise ValueError("La imagen debe ser JPEG, PNG o WEBP.")
        if len(contenido) < TAMANO_MINIMO_IMAGEN_BYTES:
            raise ValueError("La imagen es demasiado pequeña para ser legible; tome la foto de nuevo.")
        if len(contenido) > self.tamano_maximo_bytes:
            raise ValueError("La imagen excede el tamaño máximo permitido.")
        return formato[1]

    def capturar_rapido(self, solicitante_id: str, contenido: bytes, content_type: str) -> Comprobante:
        """Guarda la foto sin pedir ningún dato adicional (HU16: máximo 3 toques)."""
        solicitante_id = solicitante_id.strip()
        if not solicitante_id:
            raise ValueError("El residente que captura es obligatorio.")
        extension = self.validar_imagen(contenido, content_type)

        comprobante_id = uuid4()
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        ruta = self.uploads_dir / f"{comprobante_id}{extension}"
        ruta.write_bytes(contenido)

        # Si no hay solicitud aprobada, la foto se guarda igual y se vincula al completar los datos
        solicitud = self._solicitudes.obtener_solicitud_por_comprobar(solicitante_id)
        comprobante = Comprobante(
            id=comprobante_id,
            solicitante_id=solicitante_id,
            solicitud_id=solicitud.id if solicitud else None,
            requiere_horas=partida_requiere_horas(solicitud.partida_categoria) if solicitud else None,
            imagen_ruta=str(ruta),
        )
        self._db[comprobante.id] = comprobante
        return comprobante

    def obtener_por_id(self, comprobante_id: UUID) -> Optional[Comprobante]:
        comprobante = self._db.get(comprobante_id)
        if comprobante and comprobante.activo:
            return comprobante
        return None

    def listar(self, solicitante_id: Optional[str] = None, estado: Optional[EstadoComprobante] = None) -> List[Comprobante]:
        return [
            c for c in self._db.values()
            if c.activo
            and (solicitante_id is None or c.solicitante_id == solicitante_id)
            and (estado is None or c.estado == estado)
        ]

    def _obtener_editable(self, comprobante_id: UUID) -> Comprobante:
        comprobante = self.obtener_por_id(comprobante_id)
        if not comprobante:
            raise ComprobanteNoEncontradoError(f"Comprobante con ID {comprobante_id} no encontrado.")
        if comprobante.estado in ESTADOS_CERRADOS:
            raise EstadoNoEditableError(
                "El comprobante ya está cerrado; las correcciones se registran como ajuste o reverso."
            )
        return comprobante

    def _resolver_solicitud(self, comprobante: Comprobante, datos: ComprobanteDatos):
        """Devuelve la solicitud vinculada o la que indica el formulario, validando pertenencia."""
        solicitud_id = comprobante.solicitud_id or datos.solicitud_id
        if solicitud_id is None:
            raise ValueError("Debe seleccionar la solicitud de fondo que respalda este gasto.")
        if comprobante.solicitud_id and datos.solicitud_id and datos.solicitud_id != comprobante.solicitud_id:
            raise ValueError("El comprobante ya está vinculado a otra solicitud.")

        solicitud = self._solicitudes.obtener_por_id(solicitud_id)
        if not solicitud:
            raise ValueError(f"La solicitud {solicitud_id} no existe o fue eliminada.")
        if solicitud.solicitante_id != comprobante.solicitante_id:
            raise ValueError("La solicitud no pertenece al residente que capturó el comprobante.")
        if solicitud.estado != EstadoSolicitud.APROBADO:
            raise ValueError("Solo se pueden comprobar gastos de solicitudes aprobadas.")
        return solicitud

    @staticmethod
    def _validar_horas(datos: ComprobanteDatos, requiere_horas: bool) -> None:
        if requiere_horas and datos.horas is None:
            raise ValueError("Esta partida exige indicar las horas de maquinaria o de trabajo.")
        if not requiere_horas and datos.horas is not None:
            raise ValueError("Esta partida no se cobra por horas; deje las horas vacías.")

    def completar_datos(self, comprobante_id: UUID, datos: ComprobanteDatos) -> Comprobante:
        """Registra los datos del formulario de RF07; solo se permite en estado Borrador."""
        comprobante = self._obtener_editable(comprobante_id)
        solicitud = self._resolver_solicitud(comprobante, datos)
        requiere_horas = partida_requiere_horas(solicitud.partida_categoria)
        self._validar_horas(datos, requiere_horas)

        comprobante.solicitud_id = solicitud.id
        comprobante.requiere_horas = requiere_horas
        comprobante.datos = datos.model_copy(update={"solicitud_id": solicitud.id})
        comprobante.updated_at = datetime.now(timezone.utc)
        return comprobante

    def cerrar(self, comprobante_id: UUID) -> Comprobante:
        """Cierra la comprobación: factura queda comprobada, ticket o nota pasa a revisión (RF08)."""
        comprobante = self._obtener_editable(comprobante_id)
        if comprobante.datos is None:
            raise ValueError("Complete los datos del comprobante antes de cerrarlo.")

        if comprobante.datos.tipo == TipoComprobante.FACTURA:
            comprobante.estado = EstadoComprobante.COMPROBADO
        else:
            comprobante.estado = EstadoComprobante.REVISION_CONTABILIDAD
        comprobante.updated_at = datetime.now(timezone.utc)
        return comprobante

    def crear_ajuste(self, comprobante_id: UUID, correccion: AjusteCreate) -> Comprobante:
        """Crea un registro de Ajuste o Reverso que referencia al original sin modificarlo."""
        original = self.obtener_por_id(comprobante_id)
        if not original:
            raise ComprobanteNoEncontradoError(f"Comprobante con ID {comprobante_id} no encontrado.")
        if original.estado not in ESTADOS_CERRADOS:
            raise EstadoNoEditableError("Un comprobante en borrador se corrige editando sus datos, no con un ajuste.")
        if original.tipo_registro != TipoRegistro.ORIGINAL:
            raise EstadoNoEditableError("Las correcciones se hacen sobre el comprobante original.")
        if any(
            c.comprobante_origen_id == original.id and c.tipo_registro == TipoRegistro.REVERSO
            for c in self.listar()
        ):
            raise EstadoNoEditableError("El comprobante ya fue reversado.")

        datos = correccion.datos or original.datos
        if correccion.tipo_registro == TipoRegistro.AJUSTE:
            self._validar_horas(datos, bool(original.requiere_horas))
            datos = datos.model_copy(update={"solicitud_id": original.solicitud_id})

        # Toda corrección pasa por revisión de contabilidad
        registro = Comprobante(
            solicitante_id=original.solicitante_id,
            solicitud_id=original.solicitud_id,
            requiere_horas=original.requiere_horas,
            imagen_ruta=original.imagen_ruta,
            estado=EstadoComprobante.REVISION_CONTABILIDAD,
            tipo_registro=correccion.tipo_registro,
            comprobante_origen_id=original.id,
            motivo_correccion=correccion.motivo,
            datos=datos,
        )
        self._db[registro.id] = registro
        return registro

    def soft_delete(self, comprobante_id: UUID) -> bool:
        """Regla de Negocio Sección 8: prohibido hard delete; solo se descartan borradores."""
        comprobante = self._obtener_editable(comprobante_id)
        comprobante.activo = False
        comprobante.deleted_at = datetime.now(timezone.utc)
        comprobante.updated_at = datetime.now(timezone.utc)
        return True


# Instancia singleton del servicio
comprobante_service = ComprobanteService()
