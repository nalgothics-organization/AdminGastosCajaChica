# Generación de la entrega (build)

Este documento explica qué tipo de entregable produce el proyecto, cómo generarlo, cómo verificarlo y cómo publicarlo en la sección **Releases** de GitHub.

## 1. Tipo de entregable

El Módulo de Administración de Gastos y Caja Chica es una **aplicación web**:

| Capa | Tecnología | Ubicación |
| --- | --- | --- |
| API (backend) | Python 3.10+ con FastAPI y Uvicorn | `src/api`, `src/services`, `src/main.py` |
| Interfaz (frontend) | HTML, CSS y JavaScript estáticos servidos por la misma API en `/app` | `src/static` |
| Base de datos | PostgreSQL 16 en Docker (SQLite opcional) | `docker-compose.yml` |

Las pantallas se usan desde el navegador del celular o de la computadora; no existe una aplicación nativa para Android o iOS. Por eso:

- **No se genera APK** (paquete de Android) **ni IPA** (paquete de iOS): esos formatos solo aplican a aplicaciones móviles compiladas con Android Studio, Xcode, Flutter, React Native, etc.
- **El entregable es un archivo ZIP** con el código listo para instalar y ejecutar. Python es interpretado y el frontend no usa un empaquetador (Vite, Webpack), así que no hay una carpeta `build/` compilada: el ZIP contiene directamente los archivos que el servidor ejecuta.

## 2. Contenido del paquete

El archivo se llama `AdminGastosCajaChica-vX.Y.Z.zip` y al descomprimirlo crea la carpeta `AdminGastosCajaChica-vX.Y.Z/` con:

| Ruta | Para qué sirve |
| --- | --- |
| `src/` | API, modelos, servicios y pantallas del prototipo (`src/static`) |
| `tests/` | Pruebas automatizadas para validar la instalación |
| `requirements.txt` | Dependencias de Python |
| `docker-compose.yml` | Contenedor de PostgreSQL |
| `.env.example` | Plantilla de variables de entorno (sin secretos reales) |
| `demo.ps1` | Script que instala, prueba y levanta la demostración en Windows |
| `README.md`, `CHANGELOG.md`, `docs/BUILD.md` | Documentación de uso, cambios por versión y este documento |

Junto al ZIP se genera `AdminGastosCajaChica-vX.Y.Z.zip.sha256` con la huella SHA-256 para comprobar que el archivo no se corrompió al descargarlo.

**Nunca entran al paquete:** `.env`, la carpeta `uploads/` (fotos de comprobantes), `__pycache__/`, `.venv/` ni archivos de bases de datos locales. El ZIP se arma con `git archive`, que solo toma archivos versionados, así que lo que está en `.gitignore` queda fuera automáticamente (Acuerdo 2).

## 3. Requisitos para generar el build

- Git 2.30 o superior.
- PowerShell 5.1 o superior (incluido en Windows) para el script; en Linux/macOS basta con Git.
- Tener el repositorio actualizado con la rama `main` y, de preferencia, la etiqueta de la versión ya creada.

## 4. Generar el ZIP

### 4.1 Preparar la versión

1. Decidir el número con [Semantic Versioning](https://semver.org/lang/es/): mientras el proyecto esté en `0.y.z`, una función nueva sube el número menor (`0.1.0` → `0.2.0`) y una corrección sube el de parche (`0.2.0` → `0.2.1`).
2. Actualizar `version=` en `src/main.py` con el número nuevo.
3. Mover las entradas de `[Unreleased]` en `CHANGELOG.md` a una sección `## [X.Y.Z] - AAAA-MM-DD` y actualizar los enlaces de comparación al final del archivo.
4. Integrar esos cambios a `main` mediante Pull Request.

### 4.2 Ejecutar el script (Windows)

Desde la raíz del repositorio, con `main` actualizada:

```powershell
git switch main
git pull
python -m pytest tests -q
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -Version 0.2.0
```

Para empaquetar una etiqueta ya publicada en lugar del último commit:

```powershell
powershell -ExecutionPolicy Bypass -File .\scripts\build.ps1 -Version 0.2.0 -Ref v0.2.0
```

El resultado queda en `dist/` (carpeta ignorada por Git):

```text
dist/AdminGastosCajaChica-v0.2.0.zip
dist/AdminGastosCajaChica-v0.2.0.zip.sha256
```

### 4.3 Equivalente manual (Linux / macOS / Git Bash)

```bash
VERSION=0.2.0
mkdir -p dist
git archive --format=zip --prefix="AdminGastosCajaChica-v$VERSION/" \
  -o "dist/AdminGastosCajaChica-v$VERSION.zip" HEAD -- \
  src tests requirements.txt docker-compose.yml .env.example demo.ps1 \
  README.md CHANGELOG.md docs/BUILD.md
(cd dist && sha256sum "AdminGastosCajaChica-v$VERSION.zip" > "AdminGastosCajaChica-v$VERSION.zip.sha256")
```

## 5. Verificar el paquete antes de publicarlo

1. Comprobar la huella:

   ```bash
   cd dist && sha256sum -c AdminGastosCajaChica-v0.2.0.zip.sha256
   ```

   En PowerShell: `Get-FileHash dist\AdminGastosCajaChica-v0.2.0.zip` y comparar con el contenido del `.sha256`.

2. Descomprimir en una carpeta **fuera** del repositorio y confirmar que no contiene `.env` ni `uploads/`.
3. Instalar y probar desde esa carpeta (sección 6). Si las pruebas pasan y la página `http://127.0.0.1:8000/app/` abre, el paquete es válido.

## 6. Instalar y ejecutar desde el ZIP

Requisitos en el equipo destino: Python 3.10+ y Docker Desktop.

```powershell
Expand-Archive AdminGastosCajaChica-v0.2.0.zip -DestinationPath .
cd AdminGastosCajaChica-v0.2.0
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

`demo.ps1` instala dependencias, corre las pruebas, crea `.env` a partir de `.env.example`, levanta PostgreSQL, carga datos de ejemplo y abre el prototipo.

Instalación manual (cualquier sistema operativo):

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\Activate.ps1
pip install -r requirements.txt
cp .env.example .env             # Windows: copy .env.example .env  (cambiar la contraseña)
docker compose up -d db
python -m src.seed               # datos de ejemplo, opcional
python -m uvicorn src.main:app --host 0.0.0.0 --port 8000
```

- Prototipo: `http://127.0.0.1:8000/app/`
- Documentación de la API (Swagger): `http://127.0.0.1:8000/docs`
- Desde el celular en la misma red: `http://<IP-del-equipo>:8000/app/`

Sin Docker se puede usar SQLite descomentando `DATABASE_URL=sqlite:///./caja_chica.db` en `.env`.

## 7. Publicar en GitHub Releases

1. Crear y subir la etiqueta sobre el commit de `main` que se va a entregar:

   ```bash
   git switch main && git pull
   git tag -a v0.2.0 -m "v0.2.0"
   git push origin v0.2.0
   ```

2. En GitHub: **Releases → Draft a new release**, elegir la etiqueta `v0.2.0` y la etiqueta anterior (`v0.1.0`) como base.
3. Presionar **Generate release notes**. GitHub agrupa los Pull Requests según `.github/release.yml` (cambios incompatibles, nuevas funciones, correcciones, documentación, otros).
4. **Editar** las notas: agregar arriba un resumen en español de la versión, quitar entradas irrelevantes y aclarar si hay cambios incompatibles.
5. Arrastrar a **Attach binaries** los archivos `AdminGastosCajaChica-v0.2.0.zip` y `AdminGastosCajaChica-v0.2.0.zip.sha256` de la carpeta `dist/`.
6. Publicar con **Set as the latest release** marcado.
7. Copiar las notas editadas a la sección `## [0.2.0]` de `CHANGELOG.md` (formato Keep a Changelog) y subir el cambio mediante Pull Request.

Equivalente con GitHub CLI:

```bash
gh release create v0.2.0 dist/AdminGastosCajaChica-v0.2.0.zip dist/AdminGastosCajaChica-v0.2.0.zip.sha256 \
  --title "v0.2.0" --generate-notes --notes-start-tag v0.1.0 --draft
# Revisar y editar las notas en GitHub y después publicar el borrador
```

## 8. Lista de verificación de la entrega

- [ ] Las pruebas pasan en `main` (`python -m pytest tests -q`).
- [ ] `src/main.py` y `CHANGELOG.md` tienen el número de versión nuevo.
- [ ] La etiqueta `vX.Y.Z` existe en GitHub y apunta al commit correcto de `main`.
- [ ] El ZIP se generó con `scripts/build.ps1` y su SHA-256 coincide.
- [ ] El ZIP se probó en una carpeta limpia y no contiene `.env` ni `uploads/`.
- [ ] La release tiene notas generadas y editadas, y los dos archivos adjuntos.
- [ ] Las notas de la release están copiadas en `CHANGELOG.md`.
