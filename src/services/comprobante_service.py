"""Módulo de servicios de negocio para la comprobación de gastos.
Implementa:
- Captura rápida con solo la fotografía y vinculado automático a la solicitud (RNF01/HU16).
- Formulario de comprobación con horas de maquinaria o de trabajo condicionales (RF07/HU07).
- Gasto por cuenta del residente: se puede comprobar sin solicitud previa y queda en revisión.
- Inmutabilidad de comprobantes cerrados y correcciones por Ajuste/Reverso (AGENTS.md §8).
"""

import os
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Optional
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
from src.repositories import ComprobanteRepositorio
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
        self._db = ComprobanteRepositorio()
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

    def capturar_rapido(
        self,
        solicitante_id: str,
        contenido: bytes,
        content_type: str,
        solicitud_id: Optional[UUID] = None,
    ) -> Comprobante:
        """Guarda la foto sin pedir ningún dato adicional (HU16: máximo 3 toques).

        Si el residente ya eligió la solicitud a la que corresponde el gasto, la foto queda vinculada
        a ella; si no, se elige al completar los datos.
        """
        solicitante_id = solicitante_id.strip()
        if not solicitante_id:
            raise ValueError("El residente que captura es obligatorio.")
        solicitud = self._solicitud_del_residente(solicitud_id, solicitante_id) if solicitud_id else None
        extension = self.validar_imagen(contenido, content_type)

        comprobante_id = uuid4()
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        ruta = self.uploads_dir / f"{comprobante_id}{extension}"
        ruta.write_bytes(contenido)

        comprobante = Comprobante(
            id=comprobante_id,
            solicitante_id=solicitante_id,
            solicitud_id=solicitud.id if solicitud else None,
            requiere_horas=partida_requiere_horas(solicitud.partida_categoria) if solicitud else None,
            obra_id=solicitud.obra_id if solicitud else None,
            etapa_construccion=solicitud.etapa_construccion if solicitud else None,
            partida_categoria=solicitud.partida_categoria if solicitud else None,
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
        """Devuelve la solicitud que el residente eligió en el formulario, validando pertenencia.

        Devuelve None cuando el residente comprueba un gasto por su cuenta, sin solicitud previa:
        en ese caso el formulario debe traer la obra, la etapa y la partida (RF02).
        """
        solicitud_id = datos.solicitud_id
        if solicitud_id is None:
            if not (datos.obra_id and datos.etapa_construccion and datos.partida_categoria):
                raise ValueError(
                    "Seleccione la solicitud de fondo que respalda este gasto o indique la obra, "
                    "la etapa y la partida si lo pagó por su cuenta."
                )
            return None
        return self._solicitud_del_residente(solicitud_id, comprobante.solicitante_id)

    def _solicitud_del_residente(self, solicitud_id: UUID, solicitante_id: str):
        """La solicitud debe existir, ser del residente y estar aprobada."""
        solicitud = self._solicitudes.obtener_por_id(solicitud_id)
        if not solicitud:
            raise ValueError(f"La solicitud {solicitud_id} no existe o fue eliminada.")
        if solicitud.solicitante_id != solicitante_id:
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
        partida = solicitud.partida_categoria if solicitud else datos.partida_categoria
        requiere_horas = partida_requiere_horas(partida)
        self._validar_horas(datos, requiere_horas)

        if solicitud:
            comprobante.solicitud_id = solicitud.id
            comprobante.obra_id = solicitud.obra_id
            comprobante.etapa_construccion = solicitud.etapa_construccion
            comprobante.partida_categoria = solicitud.partida_categoria
            # La clasificación ya la aporta la solicitud; los datos no la repiten
            comprobante.datos = datos.model_copy(update={
                "solicitud_id": solicitud.id,
                "obra_id": None,
                "etapa_construccion": None,
                "partida_categoria": None,
            })
        else:
            comprobante.solicitud_id = None
            comprobante.obra_id = datos.obra_id
            comprobante.etapa_construccion = datos.etapa_construccion
            comprobante.partida_categoria = datos.partida_categoria
            comprobante.datos = datos
        comprobante.requiere_horas = requiere_horas
        comprobante.updated_at = datetime.now(timezone.utc)
        return self._db.guardar(comprobante)

    def cerrar(self, comprobante_id: UUID) -> Comprobante:
        """Cierra la comprobación: factura queda comprobada, ticket o nota pasa a revisión (RF08)."""
        comprobante = self._obtener_editable(comprobante_id)
        if comprobante.datos is None:
            raise ValueError("Complete los datos del comprobante antes de cerrarlo.")

        # Un gasto sin solicitud no tuvo autorización previa: contabilidad lo revisa aunque tenga factura
        if comprobante.datos.tipo == TipoComprobante.FACTURA and comprobante.solicitud_id is not None:
            comprobante.estado = EstadoComprobante.COMPROBADO
        else:
            comprobante.estado = EstadoComprobante.REVISION_CONTABILIDAD
        comprobante.updated_at = datetime.now(timezone.utc)
        return self._db.guardar(comprobante)

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
            if original.solicitud_id is not None:
                datos = datos.model_copy(update={"obra_id": None, "etapa_construccion": None, "partida_categoria": None})

        # Toda corrección pasa por revisión de contabilidad
        registro = Comprobante(
            solicitante_id=original.solicitante_id,
            solicitud_id=original.solicitud_id,
            requiere_horas=original.requiere_horas,
            obra_id=original.obra_id,
            etapa_construccion=original.etapa_construccion,
            partida_categoria=original.partida_categoria,
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
        self._db.guardar(comprobante)
        return True


# Instancia singleton del servicio
comprobante_service = ComprobanteService()
