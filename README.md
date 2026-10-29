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
python -m pytest tests -v


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

Los datos se guardan en memoria, así que se pierden al detener el servidor.

## Demostración

Desde la raíz del proyecto, en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

El script instala las dependencias, ejecuta los tests, levanta la API, carga dos solicitudes de ejemplo (una para Administración y otra para Dirección) y abre Swagger en `http://127.0.0.1:8000/docs`. Presiona `Ctrl+C` para detener el servidor.

Opciones: `-SinDatos` para iniciar sin solicitudes de ejemplo y `-Puerto 8001` si el puerto 8000 está ocupado.

  ## Versionado

  El proyecto sigue [Semantic Versioning](https://semver.org/lang/es/) con el formato MAJOR.MINOR.PATCH:

  - *MAJOR*: cambios incompatibles (PR con etiqueta breaking-change).
  - *MINOR*: funciones nuevas compatibles (etiqueta enhancement).
  - *PATCH*: correcciones compatibles (etiqueta bug).

  Cada versión publicada tiene un tag vX.Y.Z y una [release en GitHub](https://github.com/nalgothics-organization/AdminGastosCajaChica/releases) con notas generadas automáticamente y revisadas a mano. El
  historial completo está en [CHANGELOG.md](CHANGELOG.md).

  Mientras el proyecto esté en 0.y.z es un prototipo y la API puede cambiar.
