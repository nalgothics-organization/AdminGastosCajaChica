# Módulo de Administracipon de Gastos y Caja Chica
Prototipo de módulo de Administración de Gastos y Caja Chica 

## Miembros del equipo

* **Stella Isabel Casillas Ramírez** 
* **Mariano Jara Villasana** 
* **Juan Pablo Mata Aguirre** 
* **Carlos Jaasiel Morrison Ramírez** 
* **Paulina Giovanna Orozco de Alba**

## Roles del equipo 
JARA VILLASANA, MARIANO — 80547: Facilitador del trabajo y responsable de la demostración del producto.

CASILLAS RAMÍREZ, STELLA ISABEL — 38919: Responsable del producto y análisis

OROZCO DE ALBA, PAULINA — 79849: Equipo de desarrollo.

MATA AGUIRRE, JUAN PABLO — 79849: Equipo de desarrollo.

MORRISON RAMÍREZ, CARLOS JAASIEL — 80702: Equipo de desarrollo.

## Instalación y uso

### Requisitos

- Python 3.10 o superior (probado con 3.13)
- Git
- Docker Desktop (para la base de datos PostgreSQL)

### Instalación

bash
git clone https://github.com/nalgothics-organization/AdminGastosCajaChica.git
cd AdminGastosCajaChica
python -m venv .venv
.venv\Scripts\Activate.ps1   # Windows (PowerShell)
source .venv/bin/activate    # Linux / macOS
pip install -r requirements.txt


### Ejecutar pruebas

bash
ruff check .                # análisis estático (linter y complejidad)
python -m pytest tests -v

Qué revisa cada herramienta, los umbrales acordados y el flujo de GitHub Actions están en `docs/PRUEBAS.md`.


### Base de datos

bash
copy .env.example .env          # Windows; en Linux/macOS: cp .env.example .env
docker compose up -d db
python -m src.seed             # usuarios y datos de ejemplo (requiere CONTRASENA_DEMO; --reset para empezar de cero)


La API lee `DATABASE_URL` del archivo `.env`. Las tablas (`usuarios`, `solicitudes`, `autorizaciones` y `comprobantes`) se crean al arrancar y ningún registro se borra físicamente. Las pruebas usan SQLite en memoria y no tocan PostgreSQL.

### Levantar la API

bash
python -m uvicorn src.main:app --reload


Abre http://127.0.0.1:8000/docs para probar los endpoints desde Swagger.

### Endpoints

| Método | Ruta | Descripción |
| --- | --- | --- |
| GET | / | Estado del servicio |
| POST | /api/solicitudes | Registrar solicitud de fondo |
| GET | /api/solicitudes | Listar solicitudes activas |
| GET | /api/solicitudes/{id} | Obtener una solicitud por UUID |
| DELETE | /api/solicitudes/{id} | Borrado lógico (soft delete) |
| POST | /api/solicitudes/{id}/aprobar | Aprobar: registra autorizador, fecha y monto final |
| POST | /api/solicitudes/{id}/rechazar | Rechazar con comentario obligatorio |
| POST | /api/comprobantes/captura | Captura rápida: solo la foto del comprobante |
| GET | /api/comprobantes | Listar comprobantes (filtros `solicitante_id`, `estado`) |
| GET | /api/comprobantes/{id} | Obtener un comprobante por UUID |
| PUT | /api/comprobantes/{id}/datos | Completar datos (horas obligatorias en maquinaria y mano de obra) |
| POST | /api/comprobantes/{id}/cerrar | Cerrar: factura → Comprobado; ticket o nota → Revisión contabilidad |
| POST | /api/comprobantes/{id}/ajustes | Ajuste o reverso de un comprobante cerrado |
| DELETE | /api/comprobantes/{id} | Descartar un borrador (soft delete) |
| GET | /api/saldos | Saldos por obra: autorizado, comprobado, disponible, reembolsos pendientes, por facturar al cliente y fondo de contingencia |

Los datos se guardan en PostgreSQL y sobreviven al reiniciar la API. Las imágenes de comprobantes se guardan en la carpeta `UPLOADS_DIR` (por defecto `./uploads`, ver `.env.example`). Cada foto se lee con OCR ([RapidOCR](https://rapidai.github.io/RapidOCRDocs/)) antes de guardarse y se rechaza si sale borrosa, oscura o sin ningún monto; con `VALIDAR_LEGIBILIDAD=false` se desactiva.

### Usuarios y roles

Cada persona tiene un usuario con nombre, correo, rol (residente de obra, administración, dirección o contabilidad) y contraseña; el residente además tiene una obra asignada. `python -m src.seed` crea estos usuarios de demostración con la contraseña de `CONTRASENA_DEMO`:

| Usuario | Nombre | Rol |
| :--- | :--- | :--- |
| `RESIDENTE-PAU` | Paula Rivas | Residente de obra (OBRA-NORTE-01) |
| `RESIDENTE-JP` | Juan Pablo Ortiz | Residente de obra (OBRA-SUR-02) |
| `RESIDENTE-LUIS` | Luis Torres | Residente de obra (OBRA-NORTE-01) |
| `ADMIN-LAURA` | Laura Méndez | Administración |
| `DIR-CARLOS` | Carlos Ruiz | Dirección |
| `CONT-SOFIA` | Sofía Navarro | Contabilidad |

Solo un residente de obra activo registra solicitudes y captura comprobantes. Para aprobar o rechazar se envía únicamente `autorizador_id` (el usuario); el nombre y el rol se toman de su registro, así que contabilidad o un residente reciben 403 y un usuario inexistente 422. Las contraseñas se guardan en texto plano por decisión del equipo para el prototipo: no uses contraseñas reales. Todavía no hay inicio de sesión ni pantallas filtradas por rol (RF15/HU20).

Un fondo aprobado debe comprobarse dentro de `LIMITE_DIAS_COMPROBACION` días (por defecto 7). Si el residente tiene fondos sin comprobar por más tiempo, sus solicitudes nuevas aparecen como bloqueadas en la bandeja de autorización y `POST /api/solicitudes/{id}/aprobar` responde 423 (RF04/HU04).

Al aprobar una solicitud, administración o dirección eligen si el gasto es **cobrable al cliente** o sale del **fondo de contingencia** de la obra (campo `clasificacion`, obligatorio). Los comprobantes de la solicitud heredan esa clasificación; un gasto pagado sin solicitud la indica en el formulario. El tablero de saldos muestra lo que hay que facturar al cliente y cuánto queda del fondo de contingencia (RF14/HU15). Al arrancar, la API agrega a las tablas existentes las columnas nuevas que acepten nulos, sin borrar datos.

### Pantallas del prototipo

Con la API arriba, abre `http://127.0.0.1:8000/app/`:

| Pantalla | Ruta | Historia |
| --- | --- | --- |
| Captura de comprobante | /app/index.html | HU07, HU16 |
| Solicitar fondo | /app/solicitud.html | HU01, HU02 |
| Bandeja de autorización | /app/autorizacion.html | HU05 |
| Saldos por obra | /app/saldos.html | HU10 |

### Gasto sin solicitud previa

Un residente puede comprobar un gasto que pagó por su cuenta, sin solicitud aprobada: en el formulario elige *Lo pagué por mi cuenta* e indica obra, etapa y partida. Ese comprobante siempre queda en *Revisión contabilidad* y el tablero lo suma como *Pagado sin solicitud* (reembolso pendiente). Si el residente tiene una solicitud aprobada, la foto se vincula automáticamente a la más reciente.

### Captura en obra desde el celular

Con la API levantada en la red local (`python -m uvicorn src.main:app --host 0.0.0.0`), abre `http://<IP-de-tu-equipo>:8000/app/` en el celular. La primera vez pide el ID del residente; después, la captura toma 3 toques: **Fotografiar comprobante**, obturador y **Usar foto**. Los datos del comprobante se completan después desde la lista *Por completar*.

## Demostración

Desde la raíz del proyecto, en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

El script instala las dependencias, ejecuta los tests, levanta PostgreSQL en Docker, carga datos de ejemplo (5 solicitudes y 4 comprobantes en 2 obras), arranca la API y abre el tablero de saldos en `http://127.0.0.1:8000/app/saldos.html`. Presiona `Ctrl+C` para detener el servidor; la base de datos sigue en Docker.

Opciones: `-SinDatos` para iniciar sin datos de ejemplo, `-Reiniciar` para borrar la base y volver a cargarlos, y `-Puerto 8001` si el puerto 8000 está ocupado.

  ## Versionado

  El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/) con el formato MAJOR.MINOR.PATCH:

  - *MAJOR*: cambios incompatibles (PR con etiqueta breaking-change).
  - *MINOR*: funciones nuevas compatibles (etiqueta enhancement).
  - *PATCH*: correcciones compatibles (etiqueta bug).

  Cada versión publicada tiene un tag vX.Y.Z y una [release en GitHub](https://github.com/nalgothics-organization/AdminGastosCajaChica/releases) con notas generadas automáticamente y revisadas a mano. El
  historial completo está en [CHANGELOG.md](CHANGELOG.md).

  Mientras el proyecto esté en 0.y.z es un prototipo y la API puede cambiar.
