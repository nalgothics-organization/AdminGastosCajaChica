# Prepara la demostracion: instala dependencias, corre los tests, levanta PostgreSQL en Docker,
# carga datos de ejemplo, arranca la API y abre las pantallas del prototipo.
# Uso: powershell -ExecutionPolicy Bypass -File .\demo.ps1 [-SinDatos] [-Reiniciar] [-Puerto 8000]
#   -SinDatos   no carga los datos de ejemplo
#   -Reiniciar  borra la base de datos y vuelve a cargar los datos de ejemplo

param(
  [int]$Puerto = 8000,
  [switch]$SinDatos,
  [switch]$Reiniciar
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Set-Location $PSScriptRoot
$base = "http://127.0.0.1:$Puerto"

Write-Host "`n[1/5] Instalando dependencias..." -ForegroundColor Cyan
python -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias." }

Write-Host "`n[2/5] Ejecutando tests..." -ForegroundColor Cyan
python -m pytest tests -q
if ($LASTEXITCODE -ne 0) { throw "Hay tests fallando; revisa la salida antes de presentar." }

Write-Host "`n[3/5] Levantando PostgreSQL en Docker..." -ForegroundColor Cyan
if (-not (Test-Path .env)) {
  Copy-Item .env.example .env
  Write-Host "  Se creo .env a partir de .env.example (ajusta la contrasena si lo necesitas)."
}
docker info *> $null
if ($LASTEXITCODE -ne 0) { throw "Docker no esta corriendo. Abre Docker Desktop y vuelve a intentar." }
docker compose up -d db
if ($LASTEXITCODE -ne 0) { throw "No se pudo levantar la base de datos." }
$saludable = $false
for ($i = 0; $i -lt 40 -and -not $saludable; $i++) {
  $estado = docker inspect -f "{{.State.Health.Status}}" cajachica-db
  if ($estado -eq "healthy") { $saludable = $true } else { Start-Sleep -Seconds 2 }
}
if (-not $saludable) { throw "PostgreSQL no estuvo listo a tiempo (docker logs cajachica-db)." }

if (Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue) {
  throw "El puerto $Puerto ya esta en uso. Cierra la otra instancia o usa -Puerto 8001."
}

if (-not $SinDatos) {
  Write-Host "`n[4/5] Cargando datos de ejemplo..." -ForegroundColor Cyan
  if ($Reiniciar) { python -m src.seed --reset } else { python -m src.seed }
  if ($LASTEXITCODE -ne 0) { throw "No se pudieron cargar los datos de ejemplo." }
} else {
  Write-Host "`n[4/5] Sin datos de ejemplo (-SinDatos)." -ForegroundColor Cyan
}

Write-Host "`n[5/5] Levantando la API en $base ..." -ForegroundColor Cyan
$servidor = Start-Process python -ArgumentList "-m", "uvicorn", "src.main:app", "--host", "0.0.0.0", "--port", "$Puerto" -NoNewWindow -PassThru

try {
  $listo = $false
  for ($i = 0; $i -lt 30 -and -not $listo; $i++) {
    Start-Sleep -Milliseconds 500
    try { Invoke-RestMethod "$base/" | Out-Null; $listo = $true } catch { }
  }
  if (-not $listo) { throw "La API no respondio a tiempo." }

  Start-Process "$base/app/saldos.html"
  Write-Host "`nPrototipo abierto en $base/app/  (Swagger: $base/docs)" -ForegroundColor Green
  Write-Host "Recorrido sugerido: Solicitar fondo -> Autorizacion -> Captura -> Saldos." -ForegroundColor Green
  Write-Host "Desde el celular usa http://<IP-de-tu-equipo>:$Puerto/app/ en la misma red." -ForegroundColor Green
  Write-Host "Presiona Ctrl+C para detener el servidor (la base de datos sigue en Docker).`n" -ForegroundColor Green
  Wait-Process -Id $servidor.Id
}
finally {
  if (-not $servidor.HasExited) { Stop-Process -Id $servidor.Id -Force }
}
