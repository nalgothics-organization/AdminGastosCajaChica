# Genera el paquete ZIP de entrega del prototipo (ver docs/BUILD.md).
# Uso: powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -Version 0.2.0 [-Ref v0.2.0]
#   -Version  número de versión SemVer sin la "v" (obligatorio)
#   -Ref      commit, rama o etiqueta a empaquetar (por defecto HEAD)

param(
  [Parameter(Mandatory = $true)]
  [ValidatePattern('^\d+\.\d+\.\d+$')]
  [string]$Version,
  [string]$Ref = "HEAD"
)

$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)

$nombre = "AdminGastosCajaChica-v$Version"
$salida = "dist/$nombre.zip"

# Solo se empaquetan archivos versionados: .env, uploads/ y cachés nunca entran al ZIP
$incluir = @(
  "src",
  "tests",
  "requirements.txt",
  "docker-compose.yml",
  ".env.example",
  "demo.ps1",
  "README.md",
  "CHANGELOG.md",
  "docs/BUILD.md"
)

git rev-parse --verify --quiet "$Ref^{commit}" | Out-Null
if ($LASTEXITCODE -ne 0) { throw "La referencia '$Ref' no existe." }

New-Item -ItemType Directory -Force dist | Out-Null
git archive --format=zip --prefix="$nombre/" -o $salida $Ref -- $incluir
if ($LASTEXITCODE -ne 0) { throw "git archive fallo." }

$hash = (Get-FileHash $salida -Algorithm SHA256).Hash.ToLower()
[IO.File]::WriteAllText((Join-Path (Get-Location) "$salida.sha256"), "$hash  $nombre.zip`n")

Write-Host "Paquete generado: $salida" -ForegroundColor Green
Write-Host "SHA-256: $hash"
