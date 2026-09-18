# Historias de Usuario

*   **HU01: Registro de solicitud de caja chica**
    *   **Requerimiento:** RF01
    *   **Descripción:** Como **residente de obra**, necesito solicitar fondos detallando el concepto, urgencia y monto, para poder realizar compras urgentes necesarias en el frente de obra (ej. refacciones, comidas de cuadrilla).
    *   **Criterios de aceptación:**
        *   **Dado** que necesito un material urgente, **cuando** ingreso una solicitud, **entonces** el sistema me pide adjuntar una evidencia de la necesidad.
        *   **Dado** que completo la solicitud, **cuando** la envío, **entonces** se genera un folio único y se notifica al nivel de autorización correspondiente.

*   **HU02: Clasificación forzosa del gasto**
    *   **Requerimiento:** RF02
    *   **Descripción:** Como **contabilidad**, necesito que todo gasto esté asociado obligatoriamente a una obra y partida, para poder clasificar correctamente el gasto y evitar fugas.
    *   **Criterios de aceptación:**
        *   **Dado** que el residente registra una solicitud, **cuando** intenta omitir la obra, **entonces** el sistema bloquea el envío y exige seleccionar una obra activa.
        *   **Dado** que se registra un monto, **cuando** se elige la obra, **entonces** se debe elegir obligatoriamente una categoría de gasto.

*   **HU03: Niveles de autorización escalonados**
    *   **Requerimiento:** RF03
    *   **Descripción:** Como **dirección**, necesito que los montos altos pasen por mi validación, para tener control sobre fugas de presupuesto que rebasen los límites preestablecidos.
    *   **Criterios de aceptación:**
        *   **Dado** que los montos tienen diferentes niveles de aprobación, **cuando** un residente pide un monto menor, **entonces** se asigna a administración.
        *   **Dado** que un residente solicita un monto alto, **cuando** se registra, **entonces** el sistema requiere la firma digital de dirección.

*   **HU04: Bloqueo por antigüedad de adeudo**
    *   **Requerimiento:** RF04
    *   **Descripción:** Como **administración**, necesito bloquear la entrega de fondos nuevos a residentes morosos, para forzarlos a entregar los tickets arrugados que tienen guardados.
    *   **Criterios de aceptación:**
        *   **Dado** que un residente tiene comprobaciones vencidas, **cuando** pide un nuevo fondo, **entonces** el sistema rechaza la solicitud automáticamente.
        *   **Dado** que el sistema bloquea la entrega, **cuando** el residente revisa el estado, **entonces** se le notifica que debe comprobar sus gastos anteriores primero.

*   **HU05: Autorización de caja chica**
    *   **Requerimiento:** RF05
    *   **Descripción:** Como **dirección**, necesito autorizar o rechazar solicitudes dejando comentarios, para dar trazabilidad a las decisiones de gasto.
    *   **Criterios de aceptación:**
        *   **Dado** que tengo una solicitud pendiente, **cuando** la apruebo, **entonces** queda registrado mi nombre, fecha y el monto final.
        *   **Dado** que rechazo un gasto, **cuando** confirmo la acción, **entonces** debo ingresar obligatoriamente un comentario justificando la decisión.

*   **HU06: Registro de entrega física o digital**
    *   **Requerimiento:** RF06
    *   **Descripción:** Como **administración**, necesito registrar si entregué el dinero en efectivo, tarjeta o transferencia, para rastrear de dónde salió el recurso hacia la obra.
    *   **Criterios de aceptación:**
        *   **Dado** que una solicitud está autorizada, **cuando** entrego el recurso, **entonces** el sistema me permite añadir la referencia bancaria o marcar efectivo.
        *   **Dado** que se guarda el registro de entrega, **cuando** se consulta la solicitud, **entonces** aparece el nombre de la persona que dispersó el recurso.
*   **HU07: Captura de ticket en campo**
    *   **Requerimiento:** RF07
    *   **Descripción:** Como **residente de obra**, necesito fotografiar el ticket en el momento, para no perderlo en el transcurso de los días y poder comprobar mi gasto.
    *   **Criterios de aceptación:**
        *   **Dado** que acabo de pagar, **cuando** abro la comprobación, **entonces** puedo tomar una foto directa desde el celular.
        *   **Dado** que tomo la foto, **cuando** confirmo la captura, **entonces** se guarda la imagen legible y se asocia al gasto correspondiente.
*   **HU08: Exigencia de comprobante fiscal válido**
    *   **Requerimiento:** RF08
    *   **Descripción:** Como **contabilidad**, necesito que la comprobación cuente con un comprobante válido, para asegurar la deducibilidad y cuadrar el sistema contable.
    *   **Criterios de aceptación:**
        *   **Dado** que un gasto no tiene factura, **cuando** el residente intenta cerrarlo como comprobado, **entonces** el sistema se lo impide.
        *   **Dado** que hay proveedores que no dan factura, **cuando** se ingresa una nota simple, **entonces** el sistema marca el gasto bajo un estatus de revisión especial para contabilidad.
        
*   **HU09: Conciliación de faltantes y sobrantes**
    *   **Requerimiento:** RF09
    *   **Descripción:** Como **administración**, necesito conciliar lo entregado contra lo comprobado, para gestionar las diferencias sin que se olviden o se pierdan reembolsos.
    *   **Criterios de aceptación:**
        *   **Dado** que lo gastado es menor a lo entregado, **cuando** se cierra la comprobación, **entonces** se genera un registro de "sobrante a devolver".
        *   **Dado** que el residente puso de su bolsa, **cuando** lo comprobado supera al fondo, **entonces** se detona una alerta de reembolso pendiente.

*   **HU10: Visualización de saldos en tiempo real**
    *   **Requerimiento:** RF10
    *   **Descripción:** Como **dirección**, necesito ver cuánto se lleva gastado por obra en el momento, para no enterarme a fin de mes cuando ya no hay margen de maniobra.
    *   **Criterios de aceptación:**
        *   **Dado** que consulto el tablero de una obra, **cuando** reviso la caja chica, **entonces** veo desglosado lo gastado y lo pendiente por reponer.
        *   **Dado** que un residente sube un ticket nuevo, **cuando** la aplicación se actualiza, **entonces** el saldo de "gastado" se afecta inmediatamente.

*   **HU11: Extracción automática de datos fotográficos (OCR)**
    *   **Requerimiento:** RF11
    *   **Descripción:** Como **residente de obra**, necesito que el sistema lea los datos del ticket por mí, para ahorrar tiempo de captura manual que compite con mis actividades urgentes.
    *   **Criterios de aceptación:**
        *   **Dado** que subo la fotografía de una factura, **cuando** el sistema la procesa, **entonces** extrae automáticamente el monto y proveedor.
        *   **Dado** que la extracción falla o es parcial, **cuando** reviso el resultado, **entonces** puedo editar manualmente los campos no reconocidos.

*   **HU12: Alertas de gastos sospechosos**
    *   **Requerimiento:** RF12
    *   **Descripción:** Como **administración**, necesito recibir notificaciones sobre gastos fuera de patrón, para detectar errores o abusos en la caja chica.
    *   **Criterios de aceptación:**
        *   **Dado** que un comprobante se ingresa dos veces, **cuando** el sistema procesa el folio, **entonces** lanza una alerta de "gasto repetido".
        *   **Dado** que un gasto rebasa el promedio histórico de la obra, **cuando** se registra, **entonces** se marca con una bandera de precaución para su revisión.

*   **HU13: Monitoreo de comprobaciones vencidas**
    *   **Requerimiento:** RF12
    *   **Descripción:** Como **contabilidad**, necesito detectar comprobaciones que se están acercando a su límite de tiempo, para no perder la deducibilidad fiscal a fin de mes.
    *   **Criterios de aceptación:**
        *   **Dado** que un fondo lleva semanas sin comprobarse, **cuando** alcanza el límite máximo, **entonces** se emite una alerta a contabilidad y al residente.
        *   **Dado** que el estatus cambia a vencido, **cuando** consulto los saldos, **entonces** aparece resaltado en el reporte mensual de la obra.

*   **HU14: Captura en condiciones adversas**
    *   **Requerimiento:** RNF01
    *   **Descripción:** Como **residente de obra**, necesito una interfaz extremadamente simple, para poder registrar rápidamente el ticket mientras trabajo con prisas y manos sucias.
    *   **Criterios de aceptación:**
        *   **Dado** que estoy a mitad de un colado, **cuando** abro la app, **entonces** encuentro un botón gigante de "Fotografiar comprobante".
        *   **Dado** que oprimo el botón, **cuando** tomo la foto, **entonces** el proceso completo no requiere más de 3 toques de pantalla.

*   **HU15: Resiliencia en sótanos y zonas sin red**
    *   **Requerimiento:** RNF02
    *   **Descripción:** Como **residente de obra**, necesito guardar fotos de mis recibos aunque no tenga señal, para evitar perder evidencias que capturo en sótanos o zonas alejadas.
    *   **Criterios de aceptación:**
        *   **Dado** que mi celular no tiene conexión, **cuando** capturo un gasto, **entonces** la app lo guarda en la memoria local.
        *   **Dado** que la app detecta conexión nuevamente, **cuando** me conecto a una red celular o WiFi, **entonces** todos los registros offline se envían silenciosamente a la oficina.
