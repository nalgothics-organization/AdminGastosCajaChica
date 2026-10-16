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

## Demostración

Desde la raíz del proyecto, en PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\demo.ps1
```

El script instala las dependencias, ejecuta los tests, levanta la API, carga dos solicitudes de ejemplo (una para Administración y otra para Dirección) y abre Swagger en `http://127.0.0.1:8000/docs`. Presiona `Ctrl+C` para detener el servidor.

Opciones: `-SinDatos` para iniciar sin solicitudes de ejemplo y `-Puerto 8001` si el puerto 8000 está ocupado.
