  # Changelog

  Todos los cambios relevantes de este proyecto se documentan en este archivo.

  El formato se basa en [Keep a Changelog](https://keepachangelog.com/es-ES/1.1.0/)
  y el proyecto sigue [Semantic Versioning](https://semver.org/lang/es/).

  ## [Unreleased]

  ### Added

  - Análisis estático con Ruff y regla de complejidad C901 (máximo 10), ejecutado junto con las pruebas en el flujo `.github/workflows/calidad.yml` en cada pull request. Detalle en `docs/PRUEBAS.md`.
  - Revisión de dependencias con pip-audit en el flujo de calidad y configuración de Dependabot.
  - Primera versión del escaneo rápido de comprobantes (RNF05/HU21, #68 y #69): botón "Escanear comprobante" fijo en "Mi caja chica", solicitud activa precargada, subida en segundo plano con tiempo medido y aviso para repetir fotos borrosas u oscuras. Los umbrales de la revisión se calibraron con imágenes sintéticas y falta medir los 20 s en celular.
  - Revisión de la foto con OCR (RapidOCR) al escanear: se rechazan las fotos borrosas, oscuras o sin ningún monto, y la pantalla del celular se reduce a elegir solicitud y escanear (RNF05/HU21, #68 y #69).
  - Extracción de proveedor, fecha, monto y tipo del comprobante con OCR (RF11/HU11, #29 y #30): se guarda lo que se reconoce, lo demás queda por completar, y "Comprobante enviado" abre una pantalla con la foto y los datos leídos. Las columnas nuevas de la base se agregan solas al arrancar.
  - Búsqueda de secretos con Gitleaks en el código y en todo el historial de Git en cada pull request.

  ### Security

  - `evidencia_url` solo acepta una foto subida a la API o un enlace http(s); se rechazan `javascript:`, rutas con `../` y HTML.

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

  ### Instalación

  Descargar `AdminGastosCajaChica-v0.2.0.zip` de la [release v0.2.0](https://github.com/nalgothics-organization/AdminGastosCajaChica/releases/tag/v0.2.0) y comprobar su SHA-256 con el archivo `.sha256` adjunto. Después, descomprimirlo y ejecutar `powershell -ExecutionPolicy Bypass -File .\demo.ps1`. Requisitos: Python 3.10+ y Docker Desktop. Guía completa en `docs/BUILD.md`.

  ### Pull requests incluidos

  - docs(build): document ZIP deliverable and prepare v0.2.0, por @bladeRunner08 (#80)
  - docs(changelog): add 0.1.0 release entry, por @casizzy (#63)
  - docs(iteraciones): replan iterations 6 and 7 for client change requests, por @bladeRunner08 (#75)
  - docs(requerimientos): add single-screen requirement for client change CC-01, por @jaaaaaaaaasiel (#76)
  - docs(context): add per-role section visibility matrix, por @casizzy (#77)
  - docs(requerimientos): add role-based sections requirement for client change CC-02, por @juanpismata11 (#78)
  - docs(requerimientos): prioritize fast receipt scanning for client change CC-03, por @PauAlba (#79)

  Las funcionalidades de "Added" y "Changed" se integraron a `main` mediante commits directos, por eso no aparecen como PR.

  ## [0.1.0] - 2026-10-29

  Primera versión documentada del prototipo.

  ### Added

  - Configuración `.github/release.yml` con categorías por etiqueta, incluida la de cambios incompatibles (#56, #57).
  - Sección "Versionado" en el README (#58).
  - Sección "Instalación y uso" en el README (#61).
  - Este archivo CHANGELOG.md (#59).
  - Reporte de cobertura con pytest-cov y umbral mínimo de 90 % en el flujo de calidad.

  ### Fixed

  - Título de la categoría "Otros cambios" en `.github/release.yml` (#62).

  [unreleased]: https://github.com/nalgothics-organization/AdminGastosCajaChica/compare/v0.2.0...HEAD
  [0.2.0]: https://github.com/nalgothics-organization/AdminGastosCajaChica/compare/v0.1.0...v0.2.0
  [0.1.0]: https://github.com/nalgothics-organization/AdminGastosCajaChica/releases/tag/v0.1.0

  
