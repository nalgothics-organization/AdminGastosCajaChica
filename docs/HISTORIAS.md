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
