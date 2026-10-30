"""Módulo principal de la aplicación FastAPI.
Módulo de Administración de Gastos y Caja Chica.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.catalogo_obras import router as catalogo_obras_router
from src.api.comprobantes import router as comprobantes_router
from src.api.evidencias import router as evidencias_router
from src.api.saldos import router as saldos_router
from src.api.solicitudes import router as solicitudes_router
from src.database import crear_tablas

STATIC_DIR = Path(__file__).parent / "static"


@asynccontextmanager
async def lifespan(_: FastAPI):
    # Crea las tablas que falten al arrancar; no toca las que ya existen
    crear_tablas()
    yield


app = FastAPI(
    title="Admin Gastos y Caja Chica API",
    description="API para la administración de gastos y caja chica en frentes de obra",
    version="0.1.0",
    lifespan=lifespan,
)

app.include_router(evidencias_router, prefix="/api", tags=["Solicitudes"])
app.include_router(solicitudes_router, prefix="/api", tags=["Solicitudes"])
app.include_router(comprobantes_router, prefix="/api", tags=["Comprobantes"])
app.include_router(saldos_router, prefix="/api", tags=["Saldos"])
app.include_router(catalogo_obras_router, prefix="/api", tags=["Obras"])

# Interfaces del prototipo: captura en obra (RNF01/HU16), solicitud, autorización y saldos
app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="app")


@app.get(
    "/",
    tags=["Health"],
    summary="Verificar estado del servicio",
    description="Confirma que la API está en línea.",
)
def health_check():
    return {"status": "ok", "app": "Admin Gastos y Caja Chica API"}
