# Catálogo de Requerimientos Funcionales 

| ID | Descripción | Prioridad |
| :--- | :--- | :--- |
| **RF01** | El sistema debe permitir el registro de una solicitud de fondo especificando folio, obra, solicitante, concepto, monto solicitado, urgencia, partida o categoría de gasto y evidencia de la necesidad. | Alta |
| **RF02** | El sistema debe obligar a que todo gasto registrado quede asociado a una obra específica y a una categoría; no se permitirá el registro de gastos genéricos. | Alta |
| **RF03** | El sistema debe gestionar niveles de autorización distintos dependiendo de los montos solicitados y de quién tiene la facultad para aprobarlos. | Alta |
| **RF04** | El sistema debe bloquear la autorización o entrega de un fondo nuevo si el solicitante tiene comprobaciones pendientes que superen el límite de antigüedad establecido. | Alta |
| **RF05** | El sistema debe permitir a los roles autorizadores aprobar o rechazar una solicitud, registrando quién autorizó, cuándo lo hizo, el monto autorizado y los comentarios correspondientes. | Alta |
| **RF06** | El sistema debe permitir el registro de la entrega del recurso, especificando la forma de entrega (efectivo, transferencia o tarjeta), la fecha, la referencia y la persona que entregó el dinero. | Media |



# Catálogo de Requerimientos No Funcionales (RNF)

| ID | Tipo | Descripción | Prioridad | Indicador y forma de medición |
| :--- | :--- | :--- | :--- | :--- |
| **RNF01** | Usabilidad | La interfaz de captura en obra debe requerir los mínimos toques posibles debido a que el residente captura con prisa y las manos sucias. | Alta | **Indicador:** Tiempo de captura. **Medición:** El registro fotográfico del ticket no debe superar los 3 clics/toques desde la pantalla principal. |
| **RNF02** | Fiabilidad | La captura del ticket mediante fotografía no debe perderse si ocurre en una zona sin cobertura (obra). | Alta | **Indicador:** Sincronización offline. **Medición:** El 100% de las imágenes capturadas sin conexión deben guardarse localmente y sincronizarse automáticamente en menos de 60 segundos tras recuperar la red. |
| **RNF03** | Compatibilidad | La información consolidada de los gastos debe exportarse en un formato aceptado por el sistema contable que la empresa ya tiene en operación. | Media | **Indicador:** Tasa de carga exitosa. **Medición:** Cero errores de formato al importar el archivo generado directamente en el sistema contable actual. |