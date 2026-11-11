# Catálogo de Requerimientos Funcionales (RF)

> Estimación en horas, con la misma escala usada en las historias de usuario (`docs/HISTORIAS.md`).
> La estimación de cada requerimiento es la suma de las estimaciones de sus historias de usuario.
> Cambios derivados de la entrevista con el cliente: ver `docs/ENTREVISTA.md`.
> Cambios solicitados por el cliente en la presentación de avances (CC-01 a CC-03): ver los issues con la etiqueta `cambio-cliente` y `docs/ITERACIONES.md`.

| ID | Descripción | Prioridad | Estimación (h) |
| :--- | :--- | :--- | :--- |
| **RF01** | El sistema debe permitir el registro de una solicitud de fondo especificando folio, obra, solicitante, etapa de construcción (cimentación, estructura, albañilería, instalaciones, acabados y entrega), concepto, monto solicitado, costo estimado de la actividad, urgencia, partida o categoría de gasto y evidencia de la necesidad. | Alta | 12 |
| **RF02** | El sistema debe obligar a que todo gasto registrado quede asociado a una obra activa, una etapa de construcción y una partida presupuestal; no se permitirá el registro de gastos genéricos ni sin obra. | Alta | 8 |
| **RF03** | El sistema debe gestionar niveles de autorización distintos dependiendo de los montos solicitados y de quién tiene la facultad para aprobarlos. | Alta | 10 |
| **RF04** | El sistema debe bloquear la autorización o entrega de un fondo nuevo si el solicitante tiene comprobaciones pendientes que superen el límite de antigüedad establecido, y mostrar el bloqueo junto a la solicitud en el apartado de autorizaciones de la pantalla única del administrador. | Alta | 6 |
| **RF05** | El sistema debe permitir a los roles autorizadores aprobar o rechazar una solicitud, registrando quién autorizó, cuándo lo hizo, el monto autorizado y los comentarios correspondientes. | Alta | 8 |
| **RF06** | El sistema debe permitir registrar la entrega del recurso desde la pantalla única del administrador, en cuanto se aprueba la solicitud, especificando la forma de entrega (efectivo, transferencia o tarjeta), la fecha, la referencia y la persona que entregó el dinero. | Media | 6 |
| **RF07** | El sistema debe permitir capturar la comprobación del gasto subiendo el comprobante e indicando tipo (factura, ticket o nota simple), monto comprobado, fecha del gasto, proveedor, concepto (incluidas horas de maquinaria o de trabajo cuando aplique) y una imagen legible. El gasto puede comprobarse contra una solicitud aprobada o, si el residente lo pagó por su cuenta, sin solicitud previa indicando obra, etapa y partida; en ese caso queda en revisión de contabilidad. | Alta | 10 |
| **RF08** | El sistema debe impedir que un gasto sea cerrado como "comprobado" si no cuenta con un comprobante; los gastos con factura se cierran directamente y los respaldados solo por nota simple o ticket quedan en estatus de revisión por contabilidad. | Alta | 8 |
| **RF09** | El sistema debe conciliar automáticamente el monto comprobado contra el monto entregado, exigiendo el registro de las diferencias como sobrantes devueltos, faltantes o reembolsos; la conciliación se consulta y se cierra desde la pantalla única del administrador. | Alta | 12 |
| **RF10** | El sistema debe calcular y mostrar en tiempo real los saldos por obra, desglosando el fondo asignado, lo gastado, lo comprobado, lo pendiente por comprobar y lo que falta por reponer. | Media | 12 |
| **RF11** | El sistema debe extraer automáticamente los datos clave del comprobante a partir de una fotografía para minimizar la captura manual. | Baja | 20 |
| **RF12** | El sistema debe generar alertas automáticas para detectar comprobaciones que se están venciendo, gastos repetidos o montos que se salen de su patrón habitual. | Baja | 12 |
| **RF13** | El sistema debe comparar por partida presupuestal el monto cotizado contra el gasto real acumulado y el porcentaje de avance de obra reportado, y alertar cuando el porcentaje gastado supere al porcentaje de avance. | Media | 12 |
| **RF14** | El sistema debe permitir clasificar cada gasto como cobrable al cliente o como cargo al fondo de contingencia (error de proyecto o de ejecución), y mostrar el saldo disponible de dicho fondo por obra. | Media | 6 |


# Catálogo de Requerimientos No Funcionales (RNF)

| ID | Tipo | Descripción | Prioridad | Indicador y forma de medición | Estimación (h) |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **RNF01** | Usabilidad | La interfaz de captura en obra debe requerir los mínimos toques posibles debido a que el residente captura con prisa y las manos sucias. | Alta | **Indicador:** Toques de captura. **Medición:** El registro fotográfico del ticket no debe superar los 3 toques desde la pantalla principal. | 8 |
| **RNF02** | Fiabilidad | La captura del ticket mediante fotografía no debe perderse si ocurre en una zona sin cobertura (obra). | Alta | **Indicador:** Sincronización offline. **Medición:** El 100% de las imágenes capturadas sin conexión deben guardarse localmente y sincronizarse automáticamente en menos de 60 segundos tras recuperar la red. | 16 |
| **RNF03** | Compatibilidad | La información consolidada de los gastos debe exportarse en un formato aceptado por el sistema contable que la empresa ya tiene en operación. | Media | **Indicador:** Tasa de carga exitosa. **Medición:** Cero errores de formato al importar el archivo generado directamente en el sistema contable actual. | 10 |
| **RNF04** | Usabilidad | Cada rol debe trabajar desde una sola pantalla que reúna todos los apartados que le corresponden, sin navegar entre páginas ni pestañas. La vista del administrador es la prioritaria. | Alta | **Indicador:** Cambios de pantalla por tarea. **Medición:** El administrador autoriza una solicitud, registra su entrega y consulta el saldo de la obra sin cambiar de página ni recargar (0 cambios de pantalla). | 12 |
