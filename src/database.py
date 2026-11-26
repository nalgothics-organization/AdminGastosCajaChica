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


class UsuarioTabla(Base):
    """Personas que usan el sistema con su rol; nunca se borran físicamente (baja lógica)."""

    __tablename__ = "usuarios"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    usuario: Mapped[str] = mapped_column(String(40), unique=True, index=True)
    nombre: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(120), unique=True, index=True)
    rol: Mapped[str] = mapped_column(String(30), index=True)
    # Texto plano por decisión del equipo para el prototipo (ver README)
    contrasena: Mapped[str] = mapped_column(String(128))
    obra_id: Mapped[Optional[str]] = mapped_column(String(60))
    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


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
    # Cobrable al cliente o fondo de contingencia (RF14); nula en los rechazos
    clasificacion: Mapped[Optional[str]] = mapped_column(String(30))
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
    # Cobrable al cliente o fondo de contingencia (RF14); sale de la solicitud o del formulario
    clasificacion: Mapped[Optional[str]] = mapped_column(String(30))

    # Datos del formulario de comprobación (RF07); nulos mientras el comprobante es un borrador sin datos
    tipo: Mapped[Optional[str]] = mapped_column(String(20))
    monto_comprobado: Mapped[Optional[Decimal]] = mapped_column(Numeric(14, 2))
    fecha_gasto: Mapped[Optional[date]] = mapped_column(Date)
    proveedor: Mapped[Optional[str]] = mapped_column(String(120))
    concepto: Mapped[Optional[str]] = mapped_column(Text)
    horas: Mapped[Optional[Decimal]] = mapped_column(Numeric(8, 2))
    unidad_horas: Mapped[Optional[str]] = mapped_column(String(20))

    activo: Mapped[bool] = mapped_column(Boolean, default=True)
    deleted_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))


def agregar_columnas_faltantes(motor=None) -> None:
    """Agrega a las tablas existentes las columnas opcionales nuevas del modelo.

    `create_all` crea las tablas que faltan pero no modifica las que ya existen; sin esto, una base
    creada con una versión anterior fallaría al leer una columna nueva. Solo agrega columnas que
    aceptan nulos, así que no toca ni borra datos existentes.
    """
    motor = motor or engine
    inspector = inspect(motor)
    with motor.begin() as conexion:
        for tabla in Base.metadata.sorted_tables:
            if not inspector.has_table(tabla.name):
                continue
            existentes = {columna["name"] for columna in inspector.get_columns(tabla.name)}
            for columna in tabla.columns:
                if columna.name in existentes or not columna.nullable:
                    continue
                tipo = columna.type.compile(dialect=motor.dialect)
                conexion.execute(text(f"ALTER TABLE {tabla.name} ADD COLUMN {columna.name} {tipo}"))


def crear_tablas() -> None:
    Base.metadata.create_all(engine)
    agregar_columnas_faltantes()


def reiniciar_tablas() -> None:
    """Vacía y recrea el esquema; solo para pruebas y datos de demostración."""
    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
