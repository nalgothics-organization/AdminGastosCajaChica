# Catálogo de Requerimientos Funcionales

> **Estimación:** horas, con la misma escala que las historias de usuario (2, 4, 8, 12, 16, 24). La estimación de un requerimiento es la suma de sus historias.
> **Iteración 1:** RF01 y RF02 con sus historias. **Iteración 2:** el resto del backlog.

| ID | Descripción | Prioridad | Estimación (h) | Iteración | Historias |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RF01** | El sistema debe permitir el registro de una solicitud de fondo especificando folio, obra, solicitante, etapa de construcción (cimentación, estructura, albañilería, instalaciones, acabados y entrega), concepto, monto solicitado, costo estimado de la actividad, urgencia, partida o categoría de gasto y evidencia de la necesidad. | Alta | 16 | Iteración 1 | HU01 |
| **RF02** | El sistema debe obligar a que todo gasto registrado quede asociado a una obra específica, una etapa de construcción y una partida o categoría de gasto; no se permitirá el registro de gastos genéricos. | Alta | 12 | Iteración 1 | HU02 |
| **RF03** | El sistema debe gestionar niveles de autorización distintos dependiendo de los montos solicitados y de quién tiene la facultad para aprobarlos. | Alta | 12 | Iteración 2 | HU03 |
| **RF04** | El sistema debe bloquear la autorización o entrega de un fondo nuevo si el solicitante tiene comprobaciones pendientes que superen el límite de antigüedad establecido. | Alta | 8 | Iteración 2 | HU04 |
| **RF05** | El sistema debe permitir a los roles autorizadores aprobar o rechazar una solicitud, registrando quién autorizó, cuándo lo hizo, el monto autorizado y los comentarios correspondientes. | Alta | 8 | Iteración 2 | HU05 |
| **RF06** | El sistema debe permitir el registro de la entrega del recurso, especificando la forma de entrega (efectivo, transferencia o tarjeta), la fecha, la referencia y la persona que entregó el dinero. | Media | 8 | Iteración 2 | HU06 |
| **RF07** | El sistema debe permitir capturar la comprobación del gasto subiendo el comprobante e indicando tipo (ticket, factura, nota), monto comprobado, fecha del gasto, proveedor y una imagen legible. | Alta | 16 | Iteración 2 | HU07 |
| **RF08** | El sistema debe impedir que un gasto sea cerrado como "comprobado" si no cuenta con un comprobante fiscal o documento válido configurado. | Alta | 12 | Iteración 2 | HU08 |
| **RF09** | El sistema debe conciliar automáticamente el monto comprobado contra el monto entregado, exigiendo el registro de las diferencias como sobrantes devueltos, faltantes o reembolsos. | Alta | 16 | Iteración 2 | HU09 |
| **RF10** | El sistema debe calcular y mostrar en tiempo real los saldos por obra, desglosando el fondo asignado, lo gastado, lo comprobado, lo pendiente por comprobar y lo que falta por reponer. | Media | 16 | Iteración 2 | HU10 |
| **RF11** | El sistema debe extraer automáticamente los datos clave del comprobante a partir de una fotografía para minimizar la captura manual. | Baja | 24 | Iteración 2 | HU11 |
| **RF12** | El sistema debe generar alertas automáticas para detectar comprobaciones que se están venciendo, gastos repetidos o montos que se salen de su patrón habitual. | Baja | 20 | Iteración 2 | HU12, HU13 |


# Catálogo de Requerimientos No Funcionales (RNF)

| ID | Tipo | Descripción | Prioridad | Indicador y forma de medición | Estimación (h) | Iteración | Historias |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **RNF01** | Usabilidad | La interfaz de captura en obra debe requerir los mínimos toques posibles debido a que el residente captura con prisa y las manos sucias. | Alta | **Indicador:** Tiempo de captura. **Medición:** El registro fotográfico del ticket no debe superar los 3 clics/toques desde la pantalla principal. | 12 | Iteración 2 | HU14 |
| **RNF02** | Fiabilidad | La captura del ticket mediante fotografía no debe perderse si ocurre en una zona sin cobertura (obra). | Alta | **Indicador:** Sincronización offline. **Medición:** El 100% de las imágenes capturadas sin conexión deben guardarse localmente y sincronizarse automáticamente en menos de 60 segundos tras recuperar la red. | 24 | Iteración 2 | HU15 |
| **RNF03** | Compatibilidad | La información consolidada de los gastos debe exportarse en un formato aceptado por el sistema contable que la empresa ya tiene en operación. | Media | **Indicador:** Tasa de carga exitosa. **Medición:** Cero errores de formato al importar el archivo generado directamente en el sistema contable actual. | 12 | Iteración 2 | HU16 |
