"""Módulo de servicios de negocio para el catálogo de Obras (RF02/HU02).
Implementa:
- Validación de obra activa para el registro de gastos.
- Validación de partida presupuestal perteneciente a la obra.
- Soft delete según AGENTS.md.
"""

from datetime import datetime
from decimal import Decimal
from typing import Dict, List, Optional

from src.models.obra import (
    EstadoObra,
    Obra,
    PartidaPresupuestal,
    es_partida_generica,
    normalizar_texto,
)


class ObraService:
    def __init__(self):
        # Almacén en memoria simulado para persistencia
        self._db: Dict[str, Obra] = {}

    @staticmethod
    def _clave(obra_id: str) -> str:
        return obra_id.strip().upper()

    def registrar_obra(self, obra: Obra) -> Obra:
        """Registra una obra en el catálogo; no admite duplicados ni partidas genéricas."""
        clave = self._clave(obra.id)
        if clave in self._db:
            raise ValueError(f"La obra {obra.id} ya está registrada.")
        for partida in obra.partidas:
            if es_partida_generica(partida.nombre):
                raise ValueError("No se permiten partidas genéricas en el presupuesto de la obra.")
        self._db[clave] = obra
        return obra

    def _obtener(self, obra_id: str) -> Optional[Obra]:
        if not obra_id or not obra_id.strip():
            return None
        obra = self._db.get(self._clave(obra_id))
        if obra and obra.activo:
            return obra
        return None

    def obtener_obra_activa(self, obra_id: str) -> Obra:
        """Regla RF02: todo gasto debe asociarse a una obra existente y activa."""
        obra = self._obtener(obra_id)
        if not obra or obra.estado != EstadoObra.ACTIVA:
            raise ValueError(
                f"La obra '{obra_id}' no existe o no está activa. Es obligatorio seleccionar una obra activa."
            )
        return obra

    def listar_obras_activas(self) -> List[Obra]:
        return [o for o in self._db.values() if o.activo and o.estado == EstadoObra.ACTIVA]

    def listar_partidas(self, obra_id: str) -> List[PartidaPresupuestal]:
        obra = self.obtener_obra_activa(obra_id)
        return [p for p in obra.partidas if p.activo]

    def obtener_partida(self, obra_id: str, partida: str) -> PartidaPresupuestal:
        """Regla RF02: la partida debe pertenecer al presupuesto de la obra (por clave o nombre)."""
        if not partida or not partida.strip() or es_partida_generica(partida):
            raise ValueError("No se permiten gastos genéricos; seleccione una partida presupuestal.")
        buscada = normalizar_texto(partida)
        for p in self.listar_partidas(obra_id):
            if buscada in (normalizar_texto(p.clave), normalizar_texto(p.nombre)):
                return p
        raise ValueError(
            f"La partida '{partida.strip()}' no pertenece al presupuesto de la obra '{obra_id}'."
        )

    def soft_delete(self, obra_id: str) -> bool:
        """Regla de Negocio Sección 8: Prohibido hard delete, solo soft delete."""
        obra = self._obtener(obra_id)
        if not obra:
            return False

        obra.activo = False
        obra.deleted_at = datetime.utcnow()
        obra.updated_at = datetime.utcnow()
        return True


def _cargar_obras_demo(service: ObraService) -> None:
    """Datos iniciales para uso manual de la API."""
    service.registrar_obra(
        Obra(
            id="OBRA-NORTE-01",
            nombre="Residencial Norte",
            partidas=[
                PartidaPresupuestal(clave="P-01", nombre="Renta de Maquinaria", monto_presupuestado=Decimal("50000.00")),
                PartidaPresupuestal(clave="P-02", nombre="Materiales de Cimentación", monto_presupuestado=Decimal("120000.00")),
                PartidaPresupuestal(clave="P-03", nombre="Mano de Obra", monto_presupuestado=Decimal("200000.00")),
            ],
        )
    )
    service.registrar_obra(
        Obra(
            id="OBRA-SUR-02",
            nombre="Plaza Sur",
            partidas=[
                PartidaPresupuestal(clave="P-01", nombre="Acero de Refuerzo", monto_presupuestado=Decimal("80000.00")),
                PartidaPresupuestal(clave="P-02", nombre="Instalaciones Eléctricas", monto_presupuestado=Decimal("60000.00")),
            ],
        )
    )


# Instancia singleton del servicio
obra_service = ObraService()
_cargar_obras_demo(obra_service)
