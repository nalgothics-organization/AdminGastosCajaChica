# Diagrama de Contenedores (C4 - Nivel 2)

> Abre la caja del **Módulo de Administración de Gastos y Caja Chica** del diagrama de contexto (`docs/CONTEXT.md`) y muestra las piezas que se ejecutan por separado, su tecnología y cómo se comunican. Es la propuesta para el prototipo.
>
> Issue: #47. Cada integrante completa su sección con un commit propio.

```mermaid
C4Container
  title Diagrama de contenedores - Módulo de Administración de Gastos y Caja Chica

  Person(residente, "Residente de obra", "Captura solicitudes y comprobantes desde el celular.")
  Person(oficina, "Administración, Dirección y Contabilidad", "Autorizan, concilian y consultan saldos.")

  System_Boundary(cajachica, "Módulo de Gastos y Caja Chica") {
    Container(web, "Aplicación web", "React + Vite", "Interfaces de captura, autorización y tablero de saldos. Usable desde el celular.")
    Container(api, "API REST", "Python, FastAPI", "Reglas de negocio: solicitudes, niveles de autorización, comprobación y conciliación.")
    ContainerDb(db, "Base de datos", "PostgreSQL en Docker", "Obras, solicitudes, autorizaciones, entregas, gastos y comprobantes con borrado lógico.")
    ContainerDb(archivos, "Almacenamiento de comprobantes", "Volumen de Docker", "Imágenes de comprobantes y evidencias.")
  }

  System_Ext(contable, "Sistema contable", "Sistema que la empresa ya tiene en operación.")
  System_Ext(ocr, "Servicio OCR", "Extrae los datos del comprobante.")
  System_Ext(correo, "Servicio de correo", "Envía notificaciones.")

  Rel(residente, web, "Usa", "HTTPS")
  Rel(oficina, web, "Usa", "HTTPS")
  Rel(web, api, "Consume", "JSON / HTTPS")
  Rel(api, db, "Lee y escribe", "SQL")
  Rel(api, archivos, "Guarda y lee imágenes")
  Rel(api, ocr, "Envía la foto", "HTTPS")
  Rel(api, correo, "Envía notificaciones", "SMTP")
  Rel(api, contable, "Genera archivo de exportación")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Contenedores

### Aplicación web

**Responsable:** @jaaaaaaaaasiel

_Pendiente._ Tecnología elegida, qué interfaces incluye (`docs/diseno`) y cómo se comunica con la API.

### API REST

**Responsable:** @juanpismata11

_Pendiente._ Qué expone (endpoints principales, Swagger en `/docs`) y qué reglas de negocio aplica.

### Base de datos

**Responsable:** @bladeRunner08

_Pendiente._ Cómo se levanta el contenedor, qué tablas principales tiene y cómo se cumple el borrado lógico.

### Almacenamiento de comprobantes

**Responsable:** @PauAlba

_Pendiente._ Dónde se guardan las imágenes, cómo se relacionan con el gasto y qué pasa con las capturas sin conexión (RNF02).

## Decisiones de arquitectura

**Responsable:** @casizzy

_Pendiente._ Por qué se eligió esta separación y estas tecnologías, y qué queda para iteraciones futuras (OCR, exportación contable, modo sin conexión).
