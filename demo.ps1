# Prepara la demostracion: instala dependencias, corre los tests,
# levanta la API, carga solicitudes de ejemplo y abre Swagger.
# Uso: powershell -ExecutionPolicy Bypass -File .\demo.ps1 [-SinDatos] [-Puerto 8000]

param(
  [int]$Puerto = 8000,
  [switch]$SinDatos
)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [Text.Encoding]::UTF8
Set-Location $PSScriptRoot
$base = "http://127.0.0.1:$Puerto"

Write-Host "`n[1/4] Instalando dependencias..." -ForegroundColor Cyan
python -m pip install -q --disable-pip-version-check -r requirements.txt
if ($LASTEXITCODE -ne 0) { throw "No se pudieron instalar las dependencias." }

Write-Host "`n[2/4] Ejecutando tests..." -ForegroundColor Cyan
python -m pytest tests -v
if ($LASTEXITCODE -ne 0) { throw "Hay tests fallando; revisa la salida antes de presentar." }

if (Get-NetTCPConnection -LocalPort $Puerto -State Listen -ErrorAction SilentlyContinue) {
  throw "El puerto $Puerto ya esta en uso. Cierra la otra instancia o usa -Puerto 8001."
}

Write-Host "`n[3/4] Levantando la API en $base ..." -ForegroundColor Cyan
$servidor = Start-Process python -ArgumentList "-m", "uvicorn", "src.main:app", "--port", "$Puerto" -NoNewWindow -PassThru

try {
  $listo = $false
  for ($i = 0; $i -lt 30 -and -not $listo; $i++) {
    Start-Sleep -Milliseconds 500
    try { Invoke-RestMethod "$base/" | Out-Null; $listo = $true } catch { }
  }
  if (-not $listo) { throw "La API no respondio a tiempo." }

  if (-not $SinDatos) {
    Write-Host "`n[4/4] Cargando solicitudes de ejemplo..." -ForegroundColor Cyan
    $ejemplos = @(
      @{
        obra_id = "OBRA-NORTE-01"; solicitante_id = "RESIDENTE-PAU"
        etapa_construccion = "estructura"; partida_categoria = "Renta de Maquinaria"
        concepto = "Renta de retroexcavadora para sondeo"
        monto_solicitado = "3500.00"; costo_estimado = "4000.00"; urgencia = "urgente"
        evidencia_url = "https://storage.empresa.com/evidencias/fuga_tubo_01.jpg"
      },
      @{
        obra_id = "OBRA-SUR-02"; solicitante_id = "RESIDENTE-JP"
        etapa_construccion = "acabados"; partida_categoria = "Materiales"
        concepto = "Compra de pintura y selladores para fachada"
        monto_solicitado = "18000.00"; costo_estimado = "18500.00"; urgencia = "alta"
        evidencia_url = "https://storage.empresa.com/evidencias/fachada_02.jpg"
        firma_digital_direccion = "FIRMA-DIR-001"
      }
    )
    foreach ($ejemplo in $ejemplos) {
      $cuerpo = [Text.Encoding]::UTF8.GetBytes(($ejemplo | ConvertTo-Json))
      $respuesta = Invoke-WebRequest "$base/api/solicitudes" -Method Post -Body $cuerpo -ContentType "application/json; charset=utf-8" -UseBasicParsing
      $r = [Text.Encoding]::UTF8.GetString($respuesta.RawContentStream.ToArray()) | ConvertFrom-Json
      Write-Host ("  {0} -> notificado a {1}" -f $r.solicitud.folio, $r.notificacion_enviada.destinatario_rol)
    }
  }

  Start-Process "$base/docs"
  Write-Host "`nSwagger abierto en $base/docs  (ReDoc: $base/redoc)" -ForegroundColor Green
  Write-Host "Presiona Ctrl+C para detener el servidor.`n" -ForegroundColor Green
  Wait-Process -Id $servidor.Id
}
finally {
  if (-not $servidor.HasExited) { Stop-Process -Id $servidor.Id -Force }
}
