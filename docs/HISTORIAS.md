# Historias de Usuario

> Estimación en horas, con la misma escala usada en los requerimientos (`docs/REQUERIMIENTOS.md`).
> La estimación de cada requerimiento es la suma de las estimaciones de sus historias de usuario.

*   **HU01: Registro de solicitud de caja chica**
    *   **Requerimiento:** RF01
    *   **Prioridad:** Alta
    *   **Estimación:** 12 h
    *   **Descripción:** Como **residente de obra**, necesito solicitar fondos detallando el concepto, urgencia y monto, para poder realizar compras urgentes necesarias en el frente de obra (ej. refacciones, renta de maquinaria, comidas de cuadrilla).
    *   **Criterios de aceptación:**
        *   **Dado** que necesito un material urgente, **cuando** ingreso una solicitud, **entonces** el sistema me pide adjuntar una evidencia de la necesidad.
        *   **Dado** que completo la solicitud, **cuando** la envío, **entonces** se genera un folio único y se notifica al nivel de autorización correspondiente.

*   **HU02: Clasificación obligatoria del gasto por obra y etapa de construcción**
    *   **Requerimiento:** RF02
    *   **Prioridad:** Alta
    *   **Estimación:** 8 h
    *   **Descripción:** Como **contabilidad**, necesito que todo gasto esté asociado obligatoriamente a una obra, una etapa de construcción y una partida o categoría de gasto, para poder clasificar, controlar y registrar los costos de cada actividad sin tener que identificar a mano a qué obra pertenece cada nota.
    *   **Criterios de aceptación:**
        *   **Dado** que el residente registra una solicitud, **cuando** intenta omitir la obra, **entonces** el sistema bloquea el envío y exige seleccionar una obra activa.
        *   **Dado** que se registra un gasto, **cuando** se elige la obra, **entonces** se debe elegir obligatoriamente una etapa de construcción y una categoría de gasto.
        *   **Dado** que se selecciona una etapa de construcción, **cuando** se registra una actividad, **entonces** el sistema permite especificar el concepto, el costo estimado y el monto solicitado.
        *   **Dado** que se registra un gasto, **cuando** se guarda la solicitud, **entonces** el sistema asocia el costo a la obra, la etapa y la partida seleccionadas para facilitar el seguimiento del presupuesto.

*   **HU03: Niveles de autorización escalonados**
    *   **Requerimiento:** RF03
    *   **Prioridad:** Alta
    *   **Estimación:** 10 h
    *   **Descripción:** Como **dirección**, necesito que los montos altos pasen por mi validación, para tener control sobre fugas de presupuesto que rebasen los límites preestablecidos.
    *   **Criterios de aceptación:**
        *   **Dado** que los montos tienen diferentes niveles de aprobación, **cuando** un residente pide un monto menor al límite, **entonces** la solicitud se asigna a administración.
        *   **Dado** que un residente solicita un monto mayor al límite, **cuando** se registra, **entonces** el sistema requiere la firma digital de dirección.

*   **HU04: Bloqueo por antigüedad de adeudo**
    *   **Requerimiento:** RF04
    *   **Prioridad:** Alta
    *   **Estimación:** 6 h
    *   **Descripción:** Como **administración**, necesito bloquear la entrega de fondos nuevos a residentes con comprobaciones vencidas, para forzarlos a entregar los comprobantes pendientes antes de recibir más dinero.
    *   **Criterios de aceptación:**
        *   **Dado** que un residente tiene comprobaciones vencidas, **cuando** pide un nuevo fondo, **entonces** el sistema rechaza la solicitud automáticamente.
        *   **Dado** que el sistema bloquea la entrega, **cuando** el residente revisa el estado, **entonces** se le notifica que debe comprobar sus gastos anteriores primero.
        *   **Dado** que reviso las autorizaciones en la pantalla única, **cuando** un residente tiene comprobaciones vencidas, **entonces** su solicitud aparece marcada como bloqueada con el número de comprobaciones pendientes.

*   **HU05: Autorización de caja chica**
    *   **Requerimiento:** RF05
    *   **Prioridad:** Alta
    *   **Estimación:** 8 h
    *   **Descripción:** Como **dirección**, necesito autorizar o rechazar solicitudes dejando comentarios, para dar trazabilidad a las decisiones de gasto.
    *   **Criterios de aceptación:**
        *   **Dado** que tengo una solicitud pendiente, **cuando** la apruebo, **entonces** queda registrado mi nombre, la fecha y el monto final.
        *   **Dado** que rechazo un gasto, **cuando** confirmo la acción, **entonces** debo ingresar obligatoriamente un comentario justificando la decisión.

*   **HU06: Registro de entrega física o digital**
    *   **Requerimiento:** RF06
    *   **Prioridad:** Media
    *   **Estimación:** 6 h
    *   **Descripción:** Como **administración**, necesito registrar, desde la misma pantalla donde autorizo, si entregué el dinero en efectivo, tarjeta o transferencia, para rastrear de dónde salió el recurso hacia la obra.
    *   **Criterios de aceptación:**
        *   **Dado** que una solicitud está autorizada, **cuando** entrego el recurso, **entonces** el sistema me permite añadir la referencia bancaria o marcar efectivo.
        *   **Dado** que se guarda el registro de entrega, **cuando** se consulta la solicitud, **entonces** aparece el nombre de la persona que dispersó el recurso.
        *   **Dado** que acabo de aprobar una solicitud en la pantalla única, **cuando** reviso el apartado de entregas, **entonces** la solicitud aparece lista para registrar su entrega sin cambiar de pantalla.

*   **HU07: Captura de comprobante en campo**
    *   **Requerimiento:** RF07
    *   **Prioridad:** Alta
    *   **Estimación:** 10 h
    *   **Descripción:** Como **residente de obra**, necesito fotografiar la factura, ticket o nota de libreta en el momento, para no perderla en el transcurso de los días y poder comprobar mi gasto.
    *   **Criterios de aceptación:**
        *   **Dado** que acabo de pagar, **cuando** abro la comprobación, **entonces** puedo tomar una foto directa desde el celular.
        *   **Dado** que tomo la foto, **cuando** confirmo la captura, **entonces** se guarda la imagen legible y se asocia al gasto correspondiente.
        *   **Dado** que el gasto se respalda con una nota simple, **cuando** la registro, **entonces** puedo indicar el concepto, las horas trabajadas (si aplica), el proveedor y el monto pagado.
        *   **Dado** que pagué el gasto por mi cuenta y no existe una solicitud aprobada, **cuando** completo los datos, **entonces** puedo comprobarlo indicando obra, etapa y partida, y queda en revisión de contabilidad como reembolso pendiente.

*   **HU08: Exigencia de comprobante válido**
    *   **Requerimiento:** RF08
    *   **Prioridad:** Alta
    *   **Estimación:** 8 h
    *   **Descripción:** Como **contabilidad**, necesito que toda comprobación cuente con un comprobante válido, para asegurar la deducibilidad y cuadrar el sistema contable.
    *   **Criterios de aceptación:**
        *   **Dado** que un gasto no tiene ningún comprobante adjunto, **cuando** el residente intenta cerrarlo como comprobado, **entonces** el sistema se lo impide.
        *   **Dado** que hay proveedores que no dan factura, **cuando** escaneo un ticket o una nota simple, **entonces** el gasto pasa solo al estatus de revisión especial para contabilidad.
        *   **Dado** que el gasto tiene factura, **cuando** confirmo el escaneo, **entonces** queda como comprobado sin revisión adicional ni pasos extra.

*   **HU09: Conciliación de faltantes y sobrantes**
    *   **Requerimiento:** RF09
    *   **Prioridad:** Alta
    *   **Estimación:** 12 h
    *   **Descripción:** Como **administración**, necesito conciliar lo entregado contra lo comprobado, para gestionar las diferencias sin que se olviden o se pierdan reembolsos.
    *   **Criterios de aceptación:**
        *   **Dado** que lo gastado es menor a lo entregado, **cuando** se cierra la comprobación, **entonces** se genera un registro de "sobrante a devolver".
        *   **Dado** que el residente puso dinero propio, **cuando** lo comprobado supera al fondo, **entonces** se genera una alerta de reembolso pendiente.
        *   **Dado** que estoy en la pantalla única, **cuando** reviso el apartado de conciliación, **entonces** veo por solicitud lo entregado, lo comprobado y la diferencia, y registro ahí mismo el sobrante o el reembolso.

*   **HU10: Visualización de saldos en tiempo real**
    *   **Requerimiento:** RF10
    *   **Prioridad:** Media
    *   **Estimación:** 12 h
    *   **Descripción:** Como **dirección**, necesito ver cuánto se lleva gastado por obra en el momento, para no enterarme a fin de mes cuando ya no hay margen de maniobra.
    *   **Criterios de aceptación:**
        *   **Dado** que consulto el tablero de una obra, **cuando** reviso la caja chica, **entonces** veo desglosado lo gastado y lo pendiente por reponer.
        *   **Dado** que un residente sube un comprobante nuevo, **cuando** la aplicación se actualiza, **entonces** el saldo de "gastado" se afecta inmediatamente.

*   **HU11: Extracción automática de datos fotográficos (OCR)**
    *   **Requerimiento:** RF11
    *   **Prioridad:** Alta
    *   **Estimación:** 16 h
    *   **Descripción:** Como **residente de obra**, necesito que el sistema lea el monto, la fecha y el proveedor del comprobante que escaneo, para solo confirmar los datos en lugar de escribirlos mientras atiendo la obra.
    *   **Criterios de aceptación:**
        *   **Dado** que escaneo un ticket o una factura, **cuando** el sistema procesa la foto, **entonces** precarga el monto, la fecha, el proveedor y el tipo de comprobante en menos de 5 segundos.
        *   **Dado** que la extracción falla o es parcial, **cuando** reviso el resultado, **entonces** puedo editar manualmente los campos no reconocidos.
        *   **Dado** que escaneo sin conexión, **cuando** confirmo la captura, **entonces** se guarda sin esperar la extracción y los datos se precargan al sincronizar.

*   **HU12: Alertas de gastos sospechosos**
    *   **Requerimiento:** RF12
    *   **Prioridad:** Baja
    *   **Estimación:** 6 h
    *   **Descripción:** Como **administración**, necesito recibir notificaciones sobre gastos fuera de patrón, para detectar errores o abusos en la caja chica.
    *   **Criterios de aceptación:**
        *   **Dado** que un comprobante se ingresa dos veces, **cuando** el sistema procesa el folio, **entonces** lanza una alerta de "gasto repetido".
        *   **Dado** que un gasto rebasa el promedio histórico de la obra, **cuando** se registra, **entonces** se marca con una bandera de precaución para su revisión.

*   **HU13: Monitoreo de comprobaciones vencidas**
    *   **Requerimiento:** RF12
    *   **Prioridad:** Baja
    *   **Estimación:** 6 h
    *   **Descripción:** Como **contabilidad**, necesito detectar comprobaciones que se están acercando a su límite de tiempo, para no perder la deducibilidad fiscal a fin de mes.
    *   **Criterios de aceptación:**
        *   **Dado** que un fondo lleva semanas sin comprobarse, **cuando** alcanza el límite máximo, **entonces** se emite una alerta a contabilidad y al residente.
        *   **Dado** que el estatus cambia a vencido, **cuando** consulto los saldos, **entonces** aparece resaltado en el reporte mensual de la obra.

*   **HU14: Seguimiento de gasto contra avance por partida**
    *   **Requerimiento:** RF13
    *   **Prioridad:** Media
    *   **Estimación:** 12 h
    *   **Descripción:** Como **dirección**, necesito comparar cuánto se ha gastado de cada partida contra su avance de obra, para detectar desviaciones antes de que se agote el presupuesto.
    *   **Criterios de aceptación:**
        *   **Dado** que una partida tiene un monto cotizado, **cuando** consulto la obra, **entonces** veo el porcentaje gastado y el porcentaje de avance de esa partida.
        *   **Dado** que el porcentaje gastado supera al porcentaje de avance, **cuando** se registra un nuevo gasto, **entonces** la partida se marca con una alerta de desviación.

*   **HU15: Distinción entre gasto cobrable y fondo de contingencia**
    *   **Requerimiento:** RF14
    *   **Prioridad:** Media
    *   **Estimación:** 6 h
    *   **Descripción:** Como **administración**, necesito indicar si un gasto se cobra al cliente o sale del fondo de contingencia por un error propio, para saber cuánto facturar al cliente y cuánto colchón queda en la obra.
    *   **Criterios de aceptación:**
        *   **Dado** que registro un gasto, **cuando** lo clasifico, **entonces** debo elegir entre "cobrable al cliente" o "fondo de contingencia".
        *   **Dado** que un gasto se carga al fondo de contingencia, **cuando** se guarda, **entonces** el saldo disponible del fondo de la obra se actualiza.

*   **HU16: Captura en condiciones adversas**
    *   **Requerimiento:** RNF01
    *   **Prioridad:** Alta
    *   **Estimación:** 8 h
    *   **Descripción:** Como **residente de obra**, necesito una interfaz extremadamente simple, para poder registrar rápidamente el comprobante mientras trabajo con prisas y manos sucias.
    *   **Criterios de aceptación:**
        *   **Dado** que estoy a mitad de un colado, **cuando** abro la app, **entonces** encuentro un botón visible de "Fotografiar comprobante" en la pantalla principal.
        *   **Dado** que oprimo el botón, **cuando** tomo la foto, **entonces** el proceso completo no requiere más de 3 toques de pantalla.

*   **HU17: Resiliencia en sótanos y zonas sin red**
    *   **Requerimiento:** RNF02
    *   **Prioridad:** Alta
    *   **Estimación:** 16 h
    *   **Descripción:** Como **residente de obra**, necesito guardar fotos de mis comprobantes aunque no tenga señal, para evitar perder evidencias que capturo en sótanos o zonas alejadas.
    *   **Criterios de aceptación:**
        *   **Dado** que mi celular no tiene conexión, **cuando** capturo un gasto, **entonces** la app lo guarda en la memoria local.
        *   **Dado** que la app detecta conexión nuevamente, **cuando** me conecto a una red celular o WiFi, **entonces** todos los registros offline se envían automáticamente en menos de 60 segundos.
        *   **Dado** que escaneo sin señal, **cuando** confirmo, **entonces** veo la confirmación de inmediato con la marca "pendiente de enviar" y puedo seguir escaneando.

*   **HU18: Exportación de gastos al sistema contable**
    *   **Requerimiento:** RNF03
    *   **Prioridad:** Media
    *   **Estimación:** 10 h
    *   **Descripción:** Como **contabilidad**, necesito exportar los gastos comprobados de un periodo en el formato de nuestro sistema contable, para no volver a capturarlos a mano.
    *   **Criterios de aceptación:**
        *   **Dado** que selecciono una obra y un periodo, **cuando** genero la exportación, **entonces** obtengo un archivo con el formato que acepta el sistema contable actual.
        *   **Dado** que importo el archivo generado, **cuando** el sistema contable lo procesa, **entonces** no se presenta ningún error de formato.

*   **HU19: Pantalla única del administrador**
    *   **Requerimiento:** RNF04
    *   **Prioridad:** Alta
    *   **Estimación:** 12 h
    *   **Descripción:** Como **administración**, necesito ver en una sola pantalla las solicitudes por autorizar, las entregas por registrar, la conciliación, los saldos por obra y las alertas, para atender la caja chica sin brincar entre pestañas ni pantallas.
    *   **Criterios de aceptación:**
        *   **Dado** que entro a la aplicación como administración, **cuando** carga la pantalla, **entonces** veo en la misma página los apartados de autorizaciones pendientes, entregas por registrar, conciliación, saldos por obra y alertas, cada uno con su contador de pendientes.
        *   **Dado** que apruebo o rechazo una solicitud, **cuando** confirmo la acción, **entonces** los apartados de entregas y saldos se actualizan en la misma pantalla sin recargar la página.
        *   **Dado** que quiero concentrarme en un apartado, **cuando** lo contraigo o lo expando, **entonces** el resto de la pantalla se mantiene y no pierdo lo que estaba capturando.
        *   **Dado** que abro la pantalla desde el celular, **cuando** carga, **entonces** los apartados se apilan en una sola columna en orden de prioridad, con las autorizaciones primero.

*   **HU20: Apartados visibles según el rol**
    *   **Requerimiento:** RF15
    *   **Prioridad:** Alta
    *   **Estimación:** 10 h
    *   **Descripción:** Como **dirección**, necesito que cada persona vea solo los apartados de su rol, para que el residente no vea las autorizaciones, contabilidad no apruebe gastos y cada quien encuentre rápido lo suyo.
    *   **Criterios de aceptación:**
        *   **Dado** que inicio sesión, **cuando** el sistema identifica mi rol, **entonces** la pantalla única muestra solo los apartados que la matriz de apartados por rol asigna a ese rol.
        *   **Dado** que soy residente de obra, **cuando** abro la aplicación, **entonces** veo el botón de escanear comprobante, mis solicitudes y comprobaciones y el saldo de mi obra, pero no las autorizaciones ni la conciliación.
        *   **Dado** que soy contabilidad, **cuando** abro la aplicación, **entonces** veo la revisión de tickets y notas simples, la conciliación y los saldos, sin los botones de aprobar o rechazar.
        *   **Dado** que alguien intenta una acción fuera de su rol (por ejemplo, aprobar una solicitud siendo residente), **cuando** la API recibe la petición, **entonces** la rechaza y registra el intento.

*   **HU21: Escaneo rápido de tickets y comprobantes**
    *   **Requerimiento:** RNF05
    *   **Prioridad:** Alta
    *   **Estimación:** 8 h
    *   **Descripción:** Como **residente de obra**, necesito escanear un ticket o comprobante con un botón que siempre esté a la vista y sin llenar formularios en ese momento, para comprobar mis gastos en segundos aunque esté en plena obra.
    *   **Criterios de aceptación:**
        *   **Dado** que abro la aplicación como residente, **cuando** carga la pantalla única, **entonces** el botón "Escanear comprobante" está fijo y visible sin desplazarme.
        *   **Dado** que toco el botón, **cuando** tomo la foto, **entonces** la obra y la solicitud activa se precargan y solo confirmo con un toque.
        *   **Dado** que confirmo el escaneo, **cuando** la imagen se sube, **entonces** veo la confirmación en 20 segundos o menos y no tengo que esperar en la pantalla a que termine la subida.
        *   **Dado** que la foto salió borrosa u oscura, **cuando** el sistema la revisa, **entonces** me pide repetirla antes de guardarla.
