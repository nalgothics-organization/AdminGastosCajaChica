"""Módulo de servicios de negocio para la gestión de Solicitudes de Fondo.
Implementa:
- Generación automática de folio único (RF01/HU01).
- Reglas de notificación al nivel correspondiente (HU01).
- Asociación obligatoria a obra activa, etapa y partida presupuestal (RF02/HU02).
- Bloqueo de fondos nuevos por comprobaciones vencidas (RF04/HU04).
- Aprobación y rechazo con trazabilidad del autorizador (RF05/HU05).
- Clasificación del gasto al aprobar: cobrable al cliente o fondo de contingencia (RF14/HU15).
- Solicitante y autorizador son usuarios activos con el rol que exige cada acción.
- Soft delete e inmutabilidad según AGENTS.md.
"""

import os
from collections import defaultdict
from datetime import datetime, timedelta, timezone
from decimal import Decimal
from typing import Dict, Iterable, List, Optional, Tuple
from uuid import UUID

from src.models.comprobante import ESTADOS_CERRADOS, comprobantes_vigentes
from src.models.solicitud import (
    AprobacionCreate,
    Autorizacion,
    BloqueoAdeudo,
    DecisionAutorizacion,
    DecisionBase,
    EstadoSolicitud,
    NotificacionNivelAutorizacion,
    RechazoCreate,
    RolAutorizador,
    SolicitudFondo,
    SolicitudFondoCreate,
    SolicitudFondoResponse,
)
from src.models.usuario import RolUsuario, Usuario
from src.repositories import ComprobanteRepositorio, SolicitudRepositorio
from src.services.obra_service import ObraService, obra_service as obra_service_default
from src.services.usuario_service import RolNoPermitidoError, UsuarioService, usuario_service as usuario_service_default


class SolicitudNoEncontradaError(LookupError):
    pass


class SolicitudNoPendienteError(Exception):
    """La solicitud ya fue decidida; las correcciones se registran como ajuste (AGENTS.md §8)."""


class AutorizadorNoPermitidoError(RolNoPermitidoError):
    """El rol del autorizador no alcanza el nivel que exige el monto de la solicitud."""


class SolicitudBloqueadaError(Exception):
    """El solicitante tiene comprobaciones vencidas; no se le autoriza un fondo nuevo (RF04)."""


ROLES_AUTORIZADORES = (RolUsuario.ADMINISTRACION, RolUsuario.DIRECCION)

# Días que tiene un residente para comprobar un fondo aprobado antes de que se le bloqueen fondos nuevos
LIMITE_DIAS_COMPROBACION_DEFAULT = 7


def _limite_dias_configurado() -> int:
    valor = os.getenv("LIMITE_DIAS_COMPROBACION", str(LIMITE_DIAS_COMPROBACION_DEFAULT)).strip()
    try:
        dias = int(valor)
    except ValueError:
        raise ValueError("LIMITE_DIAS_COMPROBACION debe ser un número entero de días.")
    if dias < 0:
        raise ValueError("LIMITE_DIAS_COMPROBACION no puede ser negativo.")
    return dias


class SolicitudFondoService:
    def __init__(self, obra_service: Optional[ObraService] = None, usuario_service: Optional[UsuarioService] = None):
        # Catálogo de obras para validar obra activa y partida presupuestal (RF02)
        self._obra_service = obra_service or obra_service_default
        # Quien solicita y quien autoriza deben ser usuarios activos con el rol adecuado
        self._usuarios = usuario_service or usuario_service_default
        self._db = SolicitudRepositorio()
        # Solo se leen los comprobantes para saber qué tanto se ha comprobado de cada fondo (RF04)
        self._comprobantes = ComprobanteRepositorio()
        self.limite_dias_comprobacion = _limite_dias_configurado()
        # Reloj inyectable para que las pruebas simulen el paso de los días
        self.reloj = lambda: datetime.now(timezone.utc)
        self.notificaciones_enviadas: List[NotificacionNivelAutorizacion] = []

    def generar_folio_unico(self, obra_id: str) -> str:
        """Genera un folio único, legible y trazable por obra."""
        # Las solicitudes nunca se borran físicamente, así que el total solo crece y el folio no se repite
        secuencia = 1001 + self._db.total()
        prefijo_obra = obra_id.strip().upper().replace(" ", "")[:4]
        timestamp = datetime.now(timezone.utc).strftime("%Y%m")
        return f"SOL-{prefijo_obra}-{timestamp}-{secuencia}"

    def determinar_nivel_autorizacion(self, monto: Decimal) -> str:
        """Determina el nivel autorizador requerido según el monto (HU03/HU01).
        Límite estándar de administración: 5,000 MXN. Montos superiores requieren Dirección.
        """
        limite_administracion = Decimal("5000.00")
        if monto > limite_administracion:
            return "Dirección"
        return "Administración"

    def emitir_notificacion(self, folio: str, monto: Decimal, rol_destinatario: str) -> NotificacionNivelAutorizacion:
        """Emite la notificación al nivel de autorización correspondiente."""
        mensaje = (
            f"Nueva solicitud de fondo {folio} por un monto de ${monto:.2f} "
            f"requiere autorización del área de {rol_destinatario}."
        )
        notificacion = NotificacionNivelAutorizacion(
            destinatario_rol=rol_destinatario,
            mensaje=mensaje,
            folio=folio,
            monto=monto,
        )
        self.notificaciones_enviadas.append(notificacion)
        return notificacion

    def crear_solicitud(self, data: SolicitudFondoCreate) -> SolicitudFondoResponse:
        """Registra una solicitud de fondo, valida evidencia, genera folio y notifica."""
        solicitante = self._usuarios.exigir(data.solicitante_id, [RolUsuario.RESIDENTE], "solicitar fondos")
        # Asociación obligatoria a obra activa y partida presupuestal de esa obra
        obra = self._obra_service.obtener_obra_activa(data.obra_id)
        partida = self._obra_service.obtener_partida(obra.id, data.partida_categoria)

        # Validación de evidencia requerida (Criterio 1 HU01)
        if not data.evidencia_url or not data.evidencia_url.strip():
            raise ValueError("Es obligatorio adjuntar una evidencia de la necesidad.")

        # Validar nivel de autorización y requerir firma de dirección (HU03)
        rol_autorizador = self.determinar_nivel_autorizacion(data.monto_solicitado)
        if rol_autorizador == "Dirección" and not data.firma_digital_direccion:
            raise ValueError("Se requiere la firma digital de dirección para montos que exceden el límite de administración.")

        folio = self.generar_folio_unico(obra.id)

        nueva_solicitud = SolicitudFondo(
            folio=folio,
            obra_id=obra.id,
            solicitante_id=solicitante.usuario,
            etapa_construccion=data.etapa_construccion,
            partida_categoria=partida.nombre,
            concepto=data.concepto,
            monto_solicitado=data.monto_solicitado,
            costo_estimado=data.costo_estimado,
            urgencia=data.urgencia,
            evidencia_url=data.evidencia_url,
            firma_digital_direccion=data.firma_digital_direccion,  # Guardar firma
            nivel_autorizacion=rol_autorizador,
            estado=EstadoSolicitud.PENDIENTE,
            activo=True,
        )

        self._db.guardar(nueva_solicitud)
        # El residente se entera al enviar la solicitud de que no se autorizará hasta que compruebe (HU04)
        self.anotar_bloqueos([nueva_solicitud])

        # Notificación al nivel autorizador correspondiente
        notificacion = self.emitir_notificacion(folio, data.monto_solicitado, rol_autorizador)

        return SolicitudFondoResponse(
            solicitud=nueva_solicitud,
            notificacion_enviada=notificacion,
        )

    def obtener_por_id(self, solicitud_id: UUID) -> Optional[SolicitudFondo]:
        solicitud = self._db.get(solicitud_id)
        if solicitud and solicitud.activo:
            return solicitud
        return None

    def obtener_por_folio(self, folio: str) -> Optional[SolicitudFondo]:
        for solicitud in self._db.values():
            if solicitud.folio == folio and solicitud.activo:
                return solicitud
        return None

    def listar_solicitudes_activas(self) -> List[SolicitudFondo]:
        return [s for s in self._db.values() if s.activo]

    def _comprobado_por_solicitud(self) -> Dict[UUID, Decimal]:
        """Suma lo comprobado de cada solicitud con los comprobantes cerrados y vigentes."""
        cerrados = [
            c for c in self._comprobantes.values()
            if c.activo and c.estado in ESTADOS_CERRADOS and c.datos is not None and c.solicitud_id
        ]
        comprobado: Dict[UUID, Decimal] = defaultdict(lambda: Decimal("0.00"))
        for comprobante in comprobantes_vigentes(cerrados):
            comprobado[comprobante.solicitud_id] += comprobante.datos.monto_comprobado
        return comprobado

    def _bloqueos_por_solicitante(self, solicitudes: Iterable[SolicitudFondo]) -> Dict[str, BloqueoAdeudo]:
        """Calcula el bloqueo de cada solicitante a partir de sus fondos aprobados sin comprobar.

        Una comprobación está vencida cuando el fondo se aprobó hace más de `limite_dias_comprobacion`
        días y lo comprobado todavía no cubre el monto autorizado (RF04/HU04).
        """
        comprobado = self._comprobado_por_solicitud()
        fecha_limite = self.reloj() - timedelta(days=self.limite_dias_comprobacion)
        vencidas: Dict[str, List[SolicitudFondo]] = defaultdict(list)
        por_comprobar: Dict[str, Decimal] = defaultdict(lambda: Decimal("0.00"))

        for solicitud in solicitudes:
            autorizacion = solicitud.autorizacion
            if not solicitud.activo or solicitud.estado != EstadoSolicitud.APROBADO or not autorizacion:
                continue
            faltante = (autorizacion.monto_autorizado or Decimal("0.00")) - comprobado[solicitud.id]
            if faltante > 0 and autorizacion.fecha_decision < fecha_limite:
                vencidas[solicitud.solicitante_id].append(solicitud)
                por_comprobar[solicitud.solicitante_id] += faltante

        return {
            solicitante: self._crear_bloqueo(lista, por_comprobar[solicitante])
            for solicitante, lista in vencidas.items()
        }

    def _crear_bloqueo(self, vencidas: List[SolicitudFondo], monto: Decimal) -> BloqueoAdeudo:
        folios = [s.folio for s in vencidas]
        return BloqueoAdeudo(
            bloqueada=True,
            comprobaciones_vencidas=len(vencidas),
            monto_por_comprobar=monto,
            folios_vencidos=folios,
            limite_dias=self.limite_dias_comprobacion,
            mensaje=(
                f"Bloqueada: el residente tiene {len(vencidas)} comprobación(es) pendiente(s) con más de "
                f"{self.limite_dias_comprobacion} días ({', '.join(folios)}). "
                "Debe comprobar sus gastos anteriores antes de recibir un fondo nuevo."
            ),
        )

    def _sin_bloqueo(self) -> BloqueoAdeudo:
        return BloqueoAdeudo(bloqueada=False, limite_dias=self.limite_dias_comprobacion)

    def bloqueo_de(self, solicitante_id: str) -> BloqueoAdeudo:
        """Bloqueo actual del solicitante por comprobaciones vencidas (RF04)."""
        bloqueos = self._bloqueos_por_solicitante(self._db.values())
        return bloqueos.get(solicitante_id) or self._sin_bloqueo()

    def anotar_bloqueos(self, solicitudes: List[SolicitudFondo]) -> List[SolicitudFondo]:
        """Marca las solicitudes pendientes con el bloqueo de su solicitante para la bandeja de autorización."""
        if not any(s.estado == EstadoSolicitud.PENDIENTE for s in solicitudes):
            return solicitudes
        bloqueos = self._bloqueos_por_solicitante(self._db.values())
        for solicitud in solicitudes:
            if solicitud.estado == EstadoSolicitud.PENDIENTE:
                solicitud.bloqueo = bloqueos.get(solicitud.solicitante_id) or self._sin_bloqueo()
        return solicitudes

    def _obtener_pendiente(self, solicitud_id: UUID, data: DecisionBase) -> Tuple[SolicitudFondo, Usuario]:
        """Valida que la solicitud exista, siga pendiente y que el usuario pueda decidirla (RF05).

        Devuelve la solicitud y el usuario autorizador; su rol sale de su registro, no de la petición.
        """
        solicitud = self.obtener_por_id(solicitud_id)
        if not solicitud:
            raise SolicitudNoEncontradaError(f"Solicitud con ID {solicitud_id} no encontrada.")

        if solicitud.estado != EstadoSolicitud.PENDIENTE:
            raise SolicitudNoPendienteError(
                f"La solicitud {solicitud.folio} ya está en estado {solicitud.estado.value} y no puede decidirse de nuevo."
            )

        autorizador = self._usuarios.exigir(data.autorizador_id, ROLES_AUTORIZADORES, "decidir solicitudes de fondo")

        # Dirección puede decidir cualquier nivel; Administración solo los de su límite
        if solicitud.nivel_autorizacion == RolAutorizador.DIRECCION.value and autorizador.rol != RolUsuario.DIRECCION:
            raise AutorizadorNoPermitidoError(
                f"La solicitud {solicitud.folio} excede el límite de Administración y solo puede decidirla Dirección."
            )
        return solicitud, autorizador

    @staticmethod
    def _datos_autorizador(autorizador: Usuario) -> dict:
        return {
            "autorizador_id": autorizador.usuario,
            "autorizador_nombre": autorizador.nombre,
            "rol_autorizador": RolAutorizador(autorizador.rol.value),
        }

    def _registrar_decision(
        self,
        solicitud: SolicitudFondo,
        estado: EstadoSolicitud,
        autorizacion: Autorizacion,
    ) -> SolicitudFondo:
        solicitud.estado = estado
        solicitud.autorizacion = autorizacion
        solicitud.updated_at = autorizacion.fecha_decision
        return self._db.guardar(solicitud)

    def aprobar_solicitud(self, solicitud_id: UUID, data: AprobacionCreate) -> SolicitudFondo:
        """Aprueba la solicitud registrando autorizador, fecha y monto final (HU05 criterio 1)."""
        solicitud, autorizador = self._obtener_pendiente(solicitud_id, data)

        # RF04: no se autoriza un fondo nuevo mientras el residente tenga comprobaciones vencidas
        bloqueo = self.bloqueo_de(solicitud.solicitante_id)
        if bloqueo.bloqueada:
            raise SolicitudBloqueadaError(f"No se puede aprobar {solicitud.folio}. {bloqueo.mensaje}")

        # RF04: no se autoriza un fondo nuevo mientras el residente tenga comprobaciones vencidas
        bloqueo = self.bloqueo_de(solicitud.solicitante_id)
        if bloqueo.bloqueada:
            raise SolicitudBloqueadaError(f"No se puede aprobar {solicitud.folio}. {bloqueo.mensaje}")

        monto_autorizado = data.monto_autorizado if data.monto_autorizado is not None else solicitud.monto_solicitado
        if monto_autorizado > solicitud.monto_solicitado:
            raise ValueError("El monto autorizado no puede ser mayor al monto solicitado.")

        autorizacion = Autorizacion(
            decision=DecisionAutorizacion.APROBADA,
            **self._datos_autorizador(autorizador),
            monto_autorizado=monto_autorizado,
            clasificacion=data.clasificacion,
            comentario=data.comentario or None,
        )
        return self._registrar_decision(solicitud, EstadoSolicitud.APROBADO, autorizacion)

    def rechazar_solicitud(self, solicitud_id: UUID, data: RechazoCreate) -> SolicitudFondo:
        """Rechaza la solicitud; el comentario justificativo es obligatorio (HU05 criterio 2)."""
        solicitud, autorizador = self._obtener_pendiente(solicitud_id, data)

        autorizacion = Autorizacion(
            decision=DecisionAutorizacion.RECHAZADA,
            **self._datos_autorizador(autorizador),
            comentario=data.comentario,
        )
        return self._registrar_decision(solicitud, EstadoSolicitud.RECHAZADO, autorizacion)

    def soft_delete(self, solicitud_id: UUID) -> bool:
        """Regla de Negocio Sección 8: Prohibido hard delete, solo soft delete."""
        solicitud = self._db.get(solicitud_id)
        if not solicitud or not solicitud.activo:
            return False

        solicitud.activo = False
        solicitud.deleted_at = datetime.now(timezone.utc)
        solicitud.updated_at = datetime.now(timezone.utc)
        self._db.guardar(solicitud)
        return True


# Instancia singleton del servicio
solicitud_service = SolicitudFondoService()
