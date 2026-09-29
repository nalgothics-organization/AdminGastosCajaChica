# Preguntas para arquitectos

## Juan Pablo
¿Cómo calculan la tarifa base de una cotizacion? ¿Tienen una matriz interna con un costo estándar por $m^2$ según la tipología del proyecto, o aplican un porcentaje sobre el costo estimado de la construcción? Si es por entregables, ¿Cómo dividen el costo total en la cotización? ¿Por porcentaje según la fase del proyecto (ej. 20% Anteproyecto, 50% Proyecto Ejecutivo, 30% Supervisión) o cada etapa se cotiza de forma independiente?

¿Qué rubros quedan fuera de la cotización inicial y se manejan como gastos reembolsables o caja chica? (ej. impresiones de planos, pago de derechos municipales, estudios de topografía/suelos, viáticos).

## Pau
¿Cómo es el proceso actual (aunque sea en papel o Excel) desde que alguien solicita un gasto de caja chica hasta que se le reembolsa o se le entrega el efectivo? ¿Quién aprueba en cada nivel y existen montos máximos por rol o por tipo de gasto (materiales vs. viáticos de instaladores vs. herramienta menor)?

¿Los gastos de caja chica se generan siempre a partir de una cotización/proyecto específico (obra), o hay gastos operativos generales sin proyecto asociado? Si están ligados a obra, ¿necesitan ver el gasto acumulado de caja chica contra el presupuesto cotizado de esa obra?

## Stella
¿Qué comprobante exigen para cerrar/justificar un gasto (factura con CFDI, ticket simple, nota sin datos fiscales)? ¿Hay gastos que se aceptan sin comprobante y bajo qué límite?

¿Cómo se reabastece la caja chica (monto fijo periódico, reposición contra comprobantes gastados, por obra o centralizada por oficina)? ¿Necesitan alertas cuando el fondo está por agotarse o cuando alguien excede su límite?

## Morrison
¿Qué flujo utilizan para la autorización y el pago de estimaciones o facturas de subcontratistas (albañilería, carpintería, instalaciones), y cómo valida el administrador que el volumen de obra cobrado realmente coincida con el avance reportado por el residente de obra antes de liberar el pago?

¿Qué nivel de desglose de partidas presupuestales manejan para clasificar un gasto de caja chica (ej. catálogo de conceptos de la obra como cimentación, albañilería, acabados, instalaciones), y el sistema debe impedir registrar un gasto si la partida ya agotó su presupuesto asignado?

## Mariano 
¿Cómo se gestionan y facturan los cambios de alcance o los imprevistos solicitados por el cliente a mitad de la obra que afectan tanto la cotización inicial como el flujo de caja chica?

¿Existe algún registro o mecanismo para auditar las discrepancias entre el costo estimado en la cotización original y el gasto real ejecutado por proyecto, permitiendo detectar desviaciones antes de que se agote el presupuesto?

# Respuestas del cliente

Resumen de la entrevista (transcripción en `entrevista.txt`). Las preguntas que no se abordaron quedan marcadas como pendientes.

## Cotización y presupuesto
* El presupuesto se arma **por partidas** (cimentación, obra gris, etc.) usando tablas tabuladas por m² y m³; no se cotiza por entregables.
* El cliente paga conforme hay **avance de obra**. El anteproyecto se cobra aunque el cliente no continúe.
* El presupuesto incluye un **porcentaje extra de contingencia** para cubrir errores de proyecto o de ejecución sin que salgan del bolsillo del despacho.

## Rubros fuera de la cotización
* **Todo** se registra: impresiones de planos, trámites, horas extras, renta de maquinaria, etc. "No hay gasto que no se registre".
* Los trámites tienen un impacto fuerte en tiempo y ese tiempo también se cobra.

## Proceso actual de caja chica
* Cada supervisor o residente tiene una caja chica para **eventualidades** (por ejemplo, rentar una retroexcavadora por hora y media).
* Hay gastos con **factura** de proveedores y otros respaldados solo con una **nota de libreta**.
* Las notas y tickets se entregan a contabilidad, que los **identifica a mano por obra**. Esos gastos se cobran al cliente, salvo que sean errores propios, que se cargan al fondo de contingencia.

## Mejoras deseadas
* Relacionar el **avance físico** de cada partida con su **presupuesto**: saber si se lleva 40 % de avance pero 50 % gastado, considerando la volatilidad de materiales (acero, PVC).
* Tener toda la información de obra **en un solo lugar**, en lugar de múltiples grupos de mensajería.

## Pendientes (no se abordaron)
* Niveles y montos de autorización por rol.
* Forma de reabastecer la caja chica y alertas de fondo agotado.
* Límite de gasto aceptado sin comprobante.
* Flujo de pago a subcontratistas.

## Impacto en requerimientos e historias
* **RF02 / HU02:** la obra, la etapa y la partida son obligatorias, porque hoy contabilidad asigna la obra a mano.
* **RF07 / HU07:** se agrega la nota simple como tipo de comprobante, con concepto y horas de maquinaria o de trabajo.
* **RF08 / HU08:** la nota simple se acepta pero queda en revisión de contabilidad; solo se bloquea el cierre sin ningún comprobante.
* **RF13 / HU14 (nuevos):** comparación de gasto real contra avance por partida.
* **RF14 / HU15 (nuevos):** clasificación del gasto como cobrable al cliente o con cargo al fondo de contingencia.
* **HU18 (nueva):** historia de usuario para RNF03 (exportación contable).
* **Renumeración:** para mantener el backlog ordenado por identificador, las historias de RNF01 y RNF02 (antes HU14 y HU15) pasan a ser HU16 y HU17.
