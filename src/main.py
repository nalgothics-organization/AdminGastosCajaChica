"""Módulo principal de la aplicación FastAPI.
Módulo de Administración de Gastos y Caja Chica.
"""

from fastapi import FastAPI
from src.api.obras import router as obras_router
from src.api.solicitudes import router as solicitudes_router

app = FastAPI(
    title="Admin Gastos y Caja Chica API",
    description="API para la administración de gastos y caja chica en frentes de obra",
    version="0.1.0",
)

app.include_router(obras_router, prefix="/api", tags=["Obras"])
app.include_router(solicitudes_router, prefix="/api", tags=["Solicitudes"])


@app.get("/")
def health_check():
    return {"status": "ok", "app": "Admin Gastos y Caja Chica API"}
