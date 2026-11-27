"""Crea en la base de datos de DATABASE_URL (.env) las tablas que falten, sin borrar ningún dato.

Uso: python -m src.crear_tablas
Crea `usuarios`, `solicitudes`, `autorizaciones` y `comprobantes` y agrega a las tablas existentes
las columnas nuevas. Nunca elimina tablas ni registros: los borrados son lógicos (`deleted_at`).
La API hace lo mismo al arrancar; este script sirve para preparar la base sin levantarla.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import sys

from sqlalchemy import inspect
from sqlalchemy.exc import OperationalError

from src.database import Base, crear_tablas, engine


def describir_tablas() -> list[str]:
    """Una línea por tabla del modelo: nombre, número de columnas y si tiene borrado lógico."""
    inspector = inspect(engine)
    lineas = []
    for tabla in Base.metadata.sorted_tables:
        columnas = {columna["name"] for columna in inspector.get_columns(tabla.name)}
        borrado = "borrado lógico (deleted_at)" if "deleted_at" in columnas else "sin cambios después de creada"
        lineas.append(f"  - {tabla.name}: {len(columnas)} columnas, {borrado}")
    return lineas


def main() -> None:
    # La URL se muestra sin la contraseña
    destino = engine.url.render_as_string(hide_password=True)
    try:
        crear_tablas()
    except OperationalError as error:
        sys.exit(
            f"No se pudo conectar a {destino}.\n"
            "Revisa que el contenedor esté arriba (docker compose up -d db) y que DATABASE_URL en .env "
            f"coincida con POSTGRES_USER, POSTGRES_PASSWORD y POSTGRES_PORT.\nDetalle: {error.orig}"
        )
    print(f"Tablas listas en {destino}:")
    print("\n".join(describir_tablas()))


if __name__ == "__main__":
    main()
