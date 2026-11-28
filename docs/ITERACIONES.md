# Objetivos por iteración

> El tablero del proyecto (GitHub Projects) agrupa las tarjetas por iteración. Aquí se registra el objetivo de cada una.

## Iteration 4

**Fechas:** 19 de octubre al 1 de noviembre de 2026

**Objetivo:** Entregar un primer prototipo navegable del flujo de caja chica: un frontend con la captura de comprobantes, la bandeja de autorización y el tablero de saldos por obra, conectado a la API y guardando la información en una base de datos PostgreSQL en contenedor. Además, documentar la arquitectura con el modelo C4 (contexto y contenedores) y diseñar las interfaces del prototipo.

**Requerimientos de la iteración:**

| Requerimiento | Historia | Responsable | Estimación (h) |
| :--- | :--- | :--- | :--- |
| RF05 - Aprobación o rechazo de solicitudes (pendiente de Iteration 3) | HU05 | @juanpismata11 | 8 |
| RF07 - Captura de comprobación del gasto | HU07 | @PauAlba | 10 |
| RF10 - Saldos por obra en tiempo real | HU10 | @jaaaaaaaaasiel | 12 |
| RNF01 - Captura con mínimos toques | HU16 | @PauAlba | 8 |

**Tareas de la iteración:** contenedor de base de datos (#48), proyecto frontend (#49), diagramas C4 (#46, #47) e interfaces (#50 a #54).

## Iteration 5 (ajustada por cambios del cliente)

**Fechas:** 2 al 15 de noviembre de 2026

**Evento:** en la presentación de avances el cliente pidió tres cambios al sistema. Cada uno se registró como issue con la etiqueta `cambio-cliente`:

| Cambio | Comentario del cliente | Decisión | Responsable | Impacto (h) | Entra en |
| :--- | :--- | :--- | :--- | :--- | :--- |
| CC-01 (#72) | Meter todo en una sola pantalla, sin que necesariamente sean pestañas | Aceptado (se empieza por el administrador) | @jaaaaaaaaasiel, con @bladeRunner08 | 40 | Iteration 6 y 7 |
| CC-02 (#73) | Definir qué roles ven qué apartados de la aplicación | Aceptado | @juanpismata11, con @casizzy | 13 | Iteration 6 |
| CC-03 (#74) | Priorizar el escaneo de tickets y comprobantes para que sea rápido y sencillo | Aceptado | @PauAlba, con @juanpismata11 | 48 | Iteration 6 y 7 |

**Objetivo ajustado:** Integrar los comentarios del cliente a la planeación. Se analiza el impacto de cada cambio, se actualizan `REQUERIMIENTOS.md`, `HISTORIAS.md`, `CONTEXT.md`, `CONTAINERS.md` y `docs/diseno` mediante un pull request por integrante, y se replanean en el tablero las iteraciones 6 y 7 para que todo lo aceptado quede listo antes de la entrega final de diciembre.

**Tareas de la iteración:**

| Tarea | Cambio | Responsable | Estimación (h) |
| :--- | :--- | :--- | :--- |
| Interfaz de pantalla única del administrador y replaneación (#70) | CC-01 | @bladeRunner08 | 4 |
| Matriz de apartados visibles por rol en `CONTEXT.md` (#71) | CC-02 | @casizzy | 3 |

Los requerimientos que estaban en la Iteration 5 sin iniciar pasan a la Iteration 6, a la Iteration 7 o quedan con la etiqueta `POSPUESTO` (ver abajo).

## Iteration 6

**Fechas:** 16 al 29 de noviembre de 2026

**Objetivo:** Reunir en una sola pantalla, sin pestañas, todo el trabajo del administrador: autorizaciones con sus bloqueos, entregas del recurso, saldos por obra y alertas. La pantalla solo muestra los apartados de cada rol. Además, entregar un escaneo de tickets y comprobantes que se inicia desde un botón fijo y confirma en 20 segundos o menos.

**Requerimientos de la iteración:**

| Requerimiento | Historia | Cambio | Responsable | Estimación (h) |
| :--- | :--- | :--- | :--- | :--- |
| RNF04 - Pantalla única por rol (#64) | HU19 (#65) | CC-01 | @jaaaaaaaaasiel | 12 |
| RF06 - Registro de entrega del recurso (#19) | HU06 (#20) | CC-01 | @jaaaaaaaaasiel | 6 |
| RF04 - Bloqueo por comprobaciones vencidas (#15) | HU04 (#16) | CC-01 | @juanpismata11 | 6 |
| RF15 - Apartados visibles según el rol (#66) | HU20 (#67) | CC-02 | @juanpismata11 | 10 |
| RNF05 - Escaneo rápido de comprobantes (#68) | HU21 (#69) | CC-03 | @PauAlba | 8 |
| RF08 - Validación de comprobante (#23) | HU08 (#24) | CC-03 | @PauAlba | 8 |

**Cierre (27 de noviembre de 2026):** se terminaron RF04, RF08 y RNF05 (22 de 50 h). RNF04, RF06 y RF15 pasan a Iteration 7 con el motivo comentado en cada tarjeta. Detalle en `docs/CIERRE_ITERACION.md`.

## Iteration 7

**Fechas:** 30 de noviembre al 13 de diciembre de 2026 (antes de la entrega final)

**Objetivo:** Completar la pantalla única del administrador con la conciliación y terminar el escaneo con dos cosas: el OCR que precarga monto, fecha y proveedor, y la captura sin señal.

**Requerimientos de la iteración:**

| Requerimiento | Historia | Cambio | Responsable | Estimación (h) |
| :--- | :--- | :--- | :--- | :--- |
| RF09 - Conciliación de sobrantes y faltantes (#25) | HU09 (#26) | CC-01 | @jaaaaaaaaasiel | 12 |
| RF11 - Extracción automática de datos (OCR) (#29) | HU11 (#30) | CC-03 | @PauAlba | 16 |
| RNF02 - Captura offline y sincronización (#40) | HU17 (#41) | CC-03 | @juanpismata11 | 16 |
| RF15 - Apartados visibles según el rol (#66), viene de Iteration 6 | HU20 (#67) | CC-02 | @juanpismata11 | 10 |
| RNF04 - Pantalla única por rol (#64), viene de Iteration 6 | HU19 (#65) | CC-01 | @jaaaaaaaaasiel | 12 |
| RF06 - Registro de entrega del recurso (#19), viene de Iteration 6 | HU06 (#20) | CC-01 | @jaaaaaaaaasiel | 6 |

## Pospuestos

No forman parte de los cambios que pidió el cliente y no caben antes de la entrega final. Quedan en el Backlog sin iteración, con la etiqueta `POSPUESTO`:

| Requerimiento | Historias | Estimación (h) |
| :--- | :--- | :--- |
| RF12 - Alertas automáticas de gastos (#31) | HU12 (#32), HU13 (#33) | 12 |
| RF13 - Gasto real contra avance por partida (#34) | HU14 (#35) | 12 |
| RF14 - Gasto cobrable al cliente o fondo de contingencia (#36) | HU15 (#37) | 6 |
| RNF03 - Exportación al sistema contable (#42) | HU18 (#43) | 10 |
