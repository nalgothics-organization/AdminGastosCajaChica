"""Módulo principal de la aplicación FastAPI.
Módulo de Administración de Gastos y Caja Chica.
"""

from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from src.api.comprobantes import router as comprobantes_router
from src.api.solicitudes import router as solicitudes_router

STATIC_DIR = Path(__file__).parent / "static"

app = FastAPI(
    title="Admin Gastos y Caja Chica API",
    description="API para la administración de gastos y caja chica en frentes de obra",
    version="0.1.0",
)

app.include_router(solicitudes_router, prefix="/api", tags=["Solicitudes"])
app.include_router(comprobantes_router, prefix="/api", tags=["Comprobantes"])

# Interfaz de captura en obra para el residente (RNF01/HU16)
app.mount("/app", StaticFiles(directory=STATIC_DIR, html=True), name="app")


@app.get(
    "/",
    tags=["Health"],
    summary="Verificar estado del servicio",
    description="Confirma que la API está en línea.",
)
def health_check():
    return {"status": "ok", "app": "Admin Gastos y Caja Chica API"}
