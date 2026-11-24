"""Conexión a la base de datos y definición de las tablas.

PostgreSQL en Docker para el prototipo (ver docker-compose.yml); SQLite en memoria para las pruebas.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import os
from datetime import date, datetime
from decimal import Decimal
from typing import Optional
from uuid import UUID

from dotenv import load_dotenv
from sqlalchemy import (
    Boolean,
    Date,
    DateTime,
    ForeignKey,
    JSON,
    Numeric,
    String,
    Text,
    Uuid,
    create_engine,
    inspect,
    text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship, sessionmaker
from sqlalchemy.pool import StaticPool

# No sobrescribe variables ya definidas (las pruebas fijan su propia URL)
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./caja_chica.db")


def _crear_engine(url: str):
    if url.startswith("sqlite"):
        opciones = {"connect_args": {"check_same_thread": False}}
        if url in ("sqlite://", "sqlite:///:memory:"):
            # Una sola conexión compartida para que la base en memoria sobreviva entre sesiones
            opciones["poolclass"] = StaticPool
        return create_engine(url, **opciones)
    return create_engine(url, pool_pre_ping=True)


engine = _crear_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, expire_on_commit=False)


class Base(DeclarativeBase):
    pass


class SolicitudTabla(Base):
    __tablename__ = "solicitudes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    folio: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    obra_id: Mapped[str] = mapped_column(String(60), index=True)
    solicitante_id: Mapped[str] = mapped_column(String(60), index=True)
    etapa_construccion: Mapped[str] = mapped_column(String(30))
    partida_categoria: Mapped[str] = mapped_column(String(80))
    concepto: Mapped[str] = mapped_column(Text)
    monto_solicitado: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    costo_estimado: Mapped[Decimal] = mapped_column(Numeric(14, 2))
    urgencia: Mapped[str] = mapped_column(String(20))
    evidencia_url: Mapped[str] = mapped_column(Text)
    firma_digital_direccion: Mapped[Optional[str]] = mapped_column(String(120))
    nivel_autorizacion: Mapped[str] = mapped_column(String(20))
    estado: Mapped[str] = mapped_column(String(20), index=True)
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    autorizacion: Mapped[Optional["AutorizacionTabla"]] = relationship(
        back_populates="solicitud", uselist=False, lazy="joined"
    )


class AutorizacionTabla(Base):
    """Decisión sobre una solicitud; el registro no se modifica una vez creado."""

    __tablename__ = "autorizaciones"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    solicitud_id: Mapped[UUID] = mapped_column(ForeignKey("solicitudes.id"), unique=True)
    decision: Mapped[str] = mapped_column(String(20))
    autorizador_id: Mapped[str] = mapped_column(String(60))
    autorizador_nombre: Mapped[str] = mapped_column(String(120))
    rol_autorizador: Mapped[str] = mapped_column(String(20))
    monto_autorizado: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    comentario: Mapped[Optional[str]] = mapped_column(Text)
    fecha_decision: Mapped[datetime] = mapped_column(DateTime(timezone=True))

    solicitud: Mapped[SolicitudTabla] = relationship(back_populates="autorizacion")


class ComprobanteTabla(Base):
    __tablename__ = "comprobantes"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    solicitante_id: Mapped[str] = mapped_column(String(60), index=True)
    solicitud_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("solicitudes.id"), index=True)
    comprobante_origen_id: Mapped[Optional[UUID]] = mapped_column(ForeignKey("comprobantes.id"))
    tipo_registro: Mapped[str] = mapped_column(String(20))
    motivo_correccion: Mapped[Optional[str]] = mapped_column(Text)
    estado: Mapped[str] = mapped_column(String(30), index=True)
    imagen_ruta: Mapped[str] = mapped_column(Text)
    requiere_horas: Mapped[Optional[bool]] = mapped_column(Boolean)

    # Clasificación del gasto (RF02); sale de la solicitud o se captura si no hay solicitud
    obra_id: Mapped[Optional[str]] = mapped_column(String(60), index=True)
    etapa_construccion: Mapped[Optional[str]] = mapped_column(String(30))
    partida_categoria: Mapped[Optional[str]] = mapped_column(String(80))

    # Datos del formulario de comprobación (RF07); nulos mientras el comprobante es un borrador sin datos
    tipo: Mapped[Optional[str]] = mapped_column(String(20))
    monto_comprobado: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    fecha_gasto: Mapped[Optional[date]] = mapped_column(Date)
    proveedor: Mapped[Optional[str]] = mapped_column(String(120))
    concepto: Mapped[Optional[str]] = mapped_column(Text)
    horas: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    unidad_horas: Mapped[Optional[str]] = mapped_column(String(20))

    # Lo que el OCR leyó de la foto (RF11); no sustituye a los datos confirmados por el residente
    lectura: Mapped[Optional[dict]] = mapped_column(JSON)

    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def agregar_columnas_faltantes() -> None:
    """Agrega a las tablas ya creadas las columnas nuevas (siempre opcionales), sin borrar ningún dato.

    `create_all` solo crea tablas que no existen; así una base de PostgreSQL de una versión anterior
    sigue funcionando sin tener que reiniciarla con `python -m src.seed --reset`.
    """
    inspector = inspect(engine)
    with engine.begin() as conexion:
        for tabla in Base.metadata.sorted_tables:
            if not inspector.has_table(tabla.name):
                continue
            existentes = {columna["name"] for columna in inspector.get_columns(tabla.name)}
            for columna in tabla.columns:
                if columna.name not in existentes and columna.nullable:
                    tipo = columna.type.compile(dialect=engine.dialect)
                    conexion.execute(text(f'ALTER TABLE "{tabla.name}" ADD COLUMN "{columna.name}" {tipo}'))


def crear_tablas() -> None:
    Base.metadata.create_all(engine)
    agregar_columnas_faltantes()


def reiniciar_tablas() -> None:
    """Vacía y recrea el esquema; solo para pruebas y datos de demostración."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
