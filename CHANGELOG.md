  # Changelog

  Todos los cambios relevantes de este proyecto se documentan en este archivo.

  El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
  y el proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

  ## [Unreleased]

  ## [0.2.0] - 2026-11-20

  Segunda versión del prototipo. El flujo completo de caja chica ya funciona de punta a punta: solicitud de fondo con foto, aprobación o rechazo, comprobación de gastos (con o sin solicitud previa) y saldos por obra en tiempo real, con los datos guardados en PostgreSQL. La entrega incluye el paquete instalable `AdminGastosCajaChica-v0.2.0.zip` (ver `docs/BUILD.md`).

  Esta versión no tiene cambios incompatibles para quien instala desde cero. Al ser 0.y.z (desarrollo inicial según SemVer), la API todavía puede cambiar.

  ### Added

  - Clasificación obligatoria de gastos por obra, etapa y partida (RF02), con catálogo de obras (`GET /api/catalogo/obras`) y selección de obras existentes en los formularios de solicitud y de gasto.
  - Captura rápida de comprobantes (solo la foto) y formulario de comprobación de gastos (RF07/HU16).
  - Saldo de caja chica por obra en la pantalla del residente, con comprobantes ligados a la solicitud elegida; "Mi caja chica" reúne en una sola pantalla la elección de solicitud, el resumen y la carga del comprobante.
  - Paquete instalable ZIP, script `scripts/build.ps1` y guía `docs/BUILD.md` para generar y publicar la entrega.
  - Diagrama de flujo en Mermaid a partir de los requerimientos (`docs/DIAGRAMA_FLUJO.md`).
  - Requerimientos y replaneación de las iteraciones 6 y 7 por las solicitudes de cambio del cliente: pantalla única (CC-01, #75, #76), secciones por rol (CC-02, #77, #78) y escaneo rápido de comprobantes (CC-03, #79).
  - Base de datos PostgreSQL en Docker (`docker compose up -d db`) con tablas `solicitudes`, `autorizaciones` y `comprobantes`; los datos ya no se pierden al reiniciar la API.
  - Saldos por obra en tiempo real (RF10/HU10): `GET /api/saldos` y pantalla `/app/saldos.html`.
  - Pantallas de solicitud de fondo y bandeja de autorización, y datos de ejemplo con `python -m src.seed`.
  - Fotografía de evidencia en la solicitud de fondo: `POST /api/solicitudes/evidencia` y `GET /api/evidencias/{nombre}`; la bandeja de autorización muestra la foto.
  - Tablero de inicio con indicadores, movimientos y pendientes calculados con los datos de la API.
  - Aprobación y rechazo de solicitudes de fondo (RF05/HU05): `POST /api/solicitudes/{id}/aprobar` y `POST /api/solicitudes/{id}/rechazar` registran quién decidió, cuándo, el monto autorizado y el comentario, obligatorio al rechazar.

  ### Changed

  - Las pantallas del prototipo siguen el diseño de `docs/diseno` (barra lateral, barra superior, pestañas y tablas).
  - Los datos de ejemplo (`python -m src.seed`) generan fotos reales de evidencia en lugar de enlaces inexistentes; usa `demo.ps1 -Reiniciar` para recargarlos.
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

  [unreleased]: https://github.com/nalgothics-organization/AdminGastosCajaChica/compare/v0.2.0...HEAD
  [0.2.0]: https://github.com/nalgothics-organization/AdminGastosCajaChica/compare/v0.1.0...v0.2.0
  [0.1.0]: https://github.com/nalgothics-organization/AdminGastosCajaChica/releases/tag/v0.1.0
