  # Changelog

  Todos los cambios relevantes de este proyecto se documentan en este archivo.

  El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
  y el proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

  ## [Unreleased]

  ### Added

  - Base de datos PostgreSQL en Docker (`docker compose up -d db`) con tablas `solicitudes`, `autorizaciones` y `comprobantes`; los datos ya no se pierden al reiniciar la API.
  - Saldos por obra en tiempo real (RF10/HU10): `GET /api/saldos` y pantalla `/app/saldos.html`.
  - Pantallas de solicitud de fondo y bandeja de autorización, y datos de ejemplo con `python -m src.seed`.
  - Aprobación y rechazo de solicitudes de fondo (RF05/HU05): `POST /api/solicitudes/{id}/aprobar` y `POST /api/solicitudes/{id}/rechazar` registran quién decidió, cuándo, el monto autorizado y el comentario, obligatorio al rechazar.

  ### Changed

  - La comprobación admite gastos sin solicitud previa (RF07/HU07): el residente indica obra, etapa y partida, el comprobante queda en revisión de contabilidad y el saldo lo muestra como reembolso pendiente.

  ## [0.1.0] - 2026-10-29

  Primera versión documentada del prototipo.

  ### Added

  - Configuración `.github/release.yml` con categorías por etiqueta, incluida la de cambios incompatibles (#56, #57).
  - Sección "Versionado" en el README (#58).
  - Sección "Instalación y uso" en el README (#61).
  - Este archivo CHANGELOG.md (#59).

  ### Fixed

  - Título de la categoría "Otros cambios" en `.github/release.yml` (#62).

  [unreleased]: https://github.com/nalgothics-organization/AdminGastosCajaChica/compare/v0.1.0...HEAD
  [0.1.0]: https://github.com/nalgothics-organization/AdminGastosCajaChica/releases/tag/v0.1.0
