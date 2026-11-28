# Cierre de iteración y presentación al cliente

> **Iteración que se cierra:** Iteration 6 (16 al 29 de noviembre de 2026)
> **Versión que se presenta:** v0.3.0, instalada desde el paquete de la release antes de empezar
> **Presentación:** 12 minutos como máximo
>
> Este documento reúne el cierre del proyecto que pide la práctica: lo terminado y lo pendiente, el guion de la presentación, las historias que se demuestran, las preguntas preparadas y la retrospectiva. Cada integrante completa su parte mediante un pull request propio.

## 1. Planeado contra terminado

**Objetivo de Iteration 6:** reunir en una sola pantalla el trabajo del administrador (autorizaciones con sus bloqueos, entregas, saldos y alertas), mostrar a cada rol solo sus apartados y entregar un escaneo de comprobantes que se inicia desde un botón fijo y confirma en 20 segundos o menos.

| | Planeado | Terminado | Pasa a Iteration 7 |
| :--- | ---: | ---: | ---: |
| Tarjetas | 15 | 8 (53 %) | 7 |
| Horas estimadas (todas las tarjetas) | 201 h | 105 h (52 %) | 96 h |
| Requerimientos RF/RNF (sin contar los CC) | 6 · 50 h | 3 · 22 h (44 %) | 3 · 28 h |

Las tarjetas de cambio del cliente (CC-01 40 h, CC-02 13 h y CC-03 48 h) agrupan las horas de sus requerimientos, así que la fila de requerimientos es la que mide mejor el avance real. El mismo comparativo está publicado como status update de cierre en el tablero del proyecto.

## 2. Lo terminado

### En Iteration 6

| Requerimiento | Historia | Cambio del cliente | Qué puede hacer el usuario | Responsable | Pull request |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RNF05 - Escaneo rápido de comprobantes (#68) | HU21 (#69) | CC-03 | El residente escanea un ticket desde un botón siempre visible, solo confirma con un toque y el sistema le pide repetir la foto si salió borrosa u oscura. | @PauAlba | #90 |
| RF08 - Validación de comprobante (#23) | HU08 (#24) | CC-03 | Un gasto sin foto no se puede cerrar; la factura queda comprobada y el ticket o la nota simple pasa a revisión de contabilidad, sin pasos extra. | @PauAlba | #102 |
| RF04 - Bloqueo por comprobaciones vencidas (#15) | HU04 (#16) | CC-01 | El residente con comprobaciones vencidas no recibe fondos nuevos y administración lo ve marcado en la bandeja de autorización, con los folios pendientes. | @juanpismata11 | #101 |

También se cerraron el análisis de CC-02 (#73) y de CC-03 (#74), y quedaron integradas las revisiones de calidad y seguridad de la investigación #86 (#87, #88, #89, #98, #99).

### En todo el proyecto (hasta v0.3.0)

| Requerimiento | Historias | Iteración |
| :--- | :--- | :--- |
| RF01 - Registro de solicitud de fondo | HU01 | Iteration 3 |
| RF02 - Clasificación obligatoria por obra, etapa y partida | HU02 | Iteration 3 |
| RF03 - Niveles de autorización por monto | HU03 | Iteration 3 |
| RF05 - Aprobación o rechazo de solicitudes | HU05 | Iteration 4 |
| RF07 - Captura de comprobación del gasto | HU07 | Iteration 4 |
| RF10 - Saldos por obra en tiempo real | HU10 | Iteration 4 |
| RNF01 - Captura con mínimos toques | HU16 | Iteration 4 |
| RF04 - Bloqueo por comprobaciones vencidas | HU04 | Iteration 6 |
| RF08 - Validación de comprobante | HU08 | Iteration 6 |
| RNF05 - Escaneo rápido de comprobantes | HU21 | Iteration 6 |

## 3. Lo pendiente

### Pasa de Iteration 6 a Iteration 7

Cada tarjeta quedó en Backlog de Iteration 7 con un comentario que explica por qué no se terminó.

| Requerimiento | Historia | Cambio | Por qué no se terminó | Qué se necesita del cliente | Entra en |
| :--- | :--- | :--- | :--- | :--- | :--- |
| RNF04 - Pantalla única por rol (#64) | HU19 (#65) | CC-01 (#72) | Es el cambio más grande (40 h en total) y al cierre no había un pull request integrado. Depende de los apartados por rol. | Confirmar el orden de prioridad de los apartados del administrador: autorizaciones, entregas, conciliación, saldos y alertas. | Iteration 7 |
| RF06 - Registro de entrega del recurso (#19) | HU06 (#20) | CC-01 | El registro de la entrega vive dentro de la pantalla única, que no quedó integrada. | Confirmar qué formas de entrega usan (efectivo, tarjeta, transferencia) y qué referencia piden para cada una. | Iteration 7 |
| RF15 - Apartados visibles según el rol (#66) | HU20 (#67) | CC-02 | El trabajo existe en la rama `feat/15-apartados-segun-rol-y-docker`, pero al cierre no tenía pull request ni aprobación, así que no cumple la definición de terminado. | Validar la matriz de apartados por rol de `docs/CONTEXT.md` y la lista de personas con su rol. | Iteration 7 |

### Ya planeado para Iteration 7 (30 de noviembre al 13 de diciembre)

| Requerimiento | Historia | Cambio | Estado al cierre de Iteration 6 |
| :--- | :--- | :--- | :--- |
| RF09 - Conciliación de sobrantes y faltantes (#25) | HU09 (#26) | CC-01 | En progreso |
| RF11 - Extracción automática de datos (OCR) (#29) | HU11 (#30) | CC-03 | Integrado con el PR #100; falta su criterio de captura sin señal, que depende de RNF02 |
| RNF02 - Captura offline y sincronización (#40) | HU17 (#41) | CC-03 | Sin iniciar |

**Carga de Iteration 7:** 6 requerimientos y 72 h, de las que unas 56 h siguen por hacer porque RF11 ya está integrado. Orden propuesto: apartados por rol, pantalla única, entregas y conciliación dentro de esa pantalla y, al final, la captura sin señal. Si no alcanza la capacidad, RNF02 es lo primero que se propone posponer, siempre con el acuerdo del cliente.

### Pospuestos (Backlog sin iteración, etiqueta `POSPUESTO`)

RF12 (HU12, HU13), RF13 (HU14), RF14 (HU15) y RNF03 (HU18). No forman parte de los cambios que pidió el cliente y no caben antes de la entrega final.

## 4. Guion de la presentación

**Reglas que sigue el guion:** la versión v0.3.0 está instalada antes de empezar y con datos de ejemplo cargados; se habla de lo que el usuario puede hacer, no de tecnología; no se muestran código, terminal ni tablero; máximo tres diapositivas. Al minuto 12 se detiene la presentación.

**Cuida el tiempo:** @casizzy (avisa con la mano al minuto 6, al minuto 8 y al minuto 11).

| Minuto | Bloque | Responsable | Qué se muestra |
| :--- | :--- | :--- | :--- |
| 0:00 a 1:00 | Apertura | @bladeRunner08 | Diapositivas 1 (objetivo y compromiso) y 2 (planeado contra terminado) |
| 1:00 a 2:30 | Demostración: bloqueo por comprobaciones vencidas (HU04, CC-01) | @juanpismata11 | Aplicación |
| 2:30 a 4:30 | Demostración: escaneo rápido de comprobantes (HU21, CC-03) | @PauAlba | Aplicación en el celular |
| 4:30 a 6:15 | Demostración: comprobante válido y cierre automático (HU08, CC-03) | @PauAlba | Aplicación |
| 6:15 a 7:00 | Demostración: el saldo de la obra refleja el comprobante (HU10) | @jaaaaaaaaasiel | Aplicación |
| 7:00 a 7:30 | Pendientes: pantalla única y registro de entregas (CC-01) | @jaaaaaaaaasiel | Diapositiva 3 (manejo de propuestas) |
| 7:30 a 8:00 | Pendientes: apartados por rol (CC-02) | @casizzy | Diapositiva 3 |
| 8:00 a 12:00 | Preguntas del cliente | Todos; modera @bladeRunner08 | Aplicación, si hace falta mostrar algo |

El orden de la demostración sigue el uso real: el residente pide dinero, comprueba su gasto escaneando el ticket, el comprobante se valida y la dirección ve el saldo de la obra al momento. Empieza por los cambios que pidió el cliente.

### 0:00 a 1:00 · Apertura (@bladeRunner08)

> Buenos días. Somos el equipo del módulo de Administración de Gastos y Caja Chica: Stella, Juan Pablo, Jaasiel, Paulina y yo, Mariano.
>
> En la presentación anterior ustedes nos pidieron tres cambios: reunir todo en una sola pantalla, que cada persona vea solo lo que le toca y que escanear un ticket sea rápido y sencillo. Con eso armamos esta iteración.
>
> Nos comprometimos a seis cosas: la pantalla única del administrador, el registro de la entrega del dinero, el bloqueo a quien debe comprobaciones, los apartados por rol, el escaneo rápido y la validación de que cada gasto tenga un comprobante válido.
>
> Terminamos tres de las seis: el escaneo rápido, la validación del comprobante y el bloqueo por comprobaciones vencidas, y eso es lo que les vamos a mostrar funcionando. Al final les explicamos qué quedó pendiente, por qué y qué necesitamos de ustedes para terminarlo antes de la entrega de diciembre.
>
> Empezamos con Juan Pablo.

### 1:00 a 2:30 · Bloqueo por comprobaciones vencidas (@juanpismata11)

_Lo escribe @juanpismata11 mediante pull request: qué dice, qué muestra en pantalla y con qué datos de ejemplo._

### 2:30 a 6:15 · Escaneo rápido y comprobante válido (@PauAlba)

_Lo escribe @PauAlba mediante pull request: qué dice, qué muestra en pantalla y con qué datos de ejemplo._

### 6:15 a 7:30 · Saldo de la obra y pendientes de la pantalla única (@jaaaaaaaaasiel)

_Lo escribe @jaaaaaaaaasiel mediante pull request: qué dice y qué muestra en el saldo, y cómo explica lo pendiente de CC-01 como propuesta._

### 7:30 a 8:00 · Pendientes de los apartados por rol (@casizzy)

_Lo escribe @casizzy mediante pull request: qué no se terminó, por qué, en qué iteración entra y qué se necesita del cliente._

### 8:00 a 12:00 · Preguntas del cliente

Modera @bladeRunner08 y pasa cada pregunta a quien desarrolló esa parte. Las respuestas son breves y directas. Si nadie sabe la respuesta, no se inventa: se anota en la sección 7 y se contesta al cliente por Slack.

## 5. Historias que se demuestran

Solo se presenta como terminado lo que cumple su definición de terminado y todos sus criterios de aceptación. En cada historia, quien presenta dice el criterio en voz alta y enseña el resultado en pantalla.

### HU04 - Bloqueo por antigüedad de adeudo (RF04 · CC-01) · @juanpismata11

- **Dado** que un residente tiene comprobaciones vencidas, **cuando** pide un nuevo fondo, **entonces** el sistema rechaza la solicitud automáticamente.
- **Dado** que el sistema bloquea la entrega, **cuando** el residente revisa el estado, **entonces** se le notifica que debe comprobar sus gastos anteriores primero.
- **Dado** que reviso las autorizaciones en la pantalla única, **cuando** un residente tiene comprobaciones vencidas, **entonces** su solicitud aparece marcada como bloqueada con el número de comprobaciones pendientes.

> Nota: la pantalla única todavía no existe. El tercer criterio se muestra en la bandeja de autorización, que es donde hoy se autoriza; se dice así, sin llamarla pantalla única.

### HU21 - Escaneo rápido de tickets y comprobantes (RNF05 · CC-03) · @PauAlba

- **Dado** que abro la aplicación como residente, **cuando** carga la pantalla, **entonces** el botón "Escanear comprobante" está fijo y visible sin desplazarme.
- **Dado** que toco el botón, **cuando** tomo la foto, **entonces** la obra y la solicitud activa se precargan y solo confirmo con un toque.
- **Dado** que confirmo el escaneo, **cuando** la imagen se sube, **entonces** veo la confirmación en 20 segundos o menos y no tengo que esperar en la pantalla a que termine la subida.
- **Dado** que la foto salió borrosa u oscura, **cuando** el sistema la revisa, **entonces** me pide repetirla antes de guardarla.

### HU08 - Exigencia de comprobante válido (RF08 · CC-03) · @PauAlba

- **Dado** que un gasto no tiene ningún comprobante adjunto, **cuando** el residente intenta cerrarlo como comprobado, **entonces** el sistema se lo impide.
- **Dado** que hay proveedores que no dan factura, **cuando** escaneo un ticket o una nota simple, **entonces** el gasto pasa solo al estatus de revisión especial para contabilidad.
- **Dado** que el gasto tiene factura, **cuando** confirmo el escaneo, **entonces** queda como comprobado sin revisión adicional ni pasos extra.

> Nota: la lectura automática de datos de la foto (HU11) es la que permite el cierre automático, pero HU11 todavía no cumple su criterio de captura sin señal. Se muestra como parte de HU08 y no se presenta como historia terminada.

### HU10 - Visualización de saldos en tiempo real (RF10) · @jaaaaaaaaasiel

- **Dado** que consulto el tablero de una obra, **cuando** reviso la caja chica, **entonces** veo desglosado lo gastado y lo pendiente por reponer.
- **Dado** que un residente sube un comprobante nuevo, **cuando** la aplicación se actualiza, **entonces** el saldo de "gastado" se afecta inmediatamente.

## 6. Preguntas que probablemente hará el cliente

Cada integrante agrega por pull request al menos dos preguntas de la parte que presenta, con su respuesta breve y en el lenguaje del cliente.

### Apertura y compromiso (@bladeRunner08)

**¿Por qué terminaron solo la mitad de lo que se comprometieron?**
Los tres cambios que pidieron sumaban más de 100 horas y los repartimos entre esta iteración y la siguiente. Priorizamos lo que el residente usa todos los días en obra: escanear el ticket y que el gasto quede comprobado. La pantalla única y los apartados por rol dependen uno del otro y los terminamos juntos en la siguiente iteración, antes de la entrega de diciembre.

**¿Lo que vimos hoy ya lo pueden usar en la empresa?**
Sí, como prueba. Es la versión 0.3.0, se instala con el paquete que publicamos y tiene datos de ejemplo. Para usarlo con sus obras reales nos falta que validen la lista de personas con su rol y el orden de los apartados de la pantalla del administrador.

**Si no alcanza el tiempo para todo en diciembre, ¿qué se queda fuera?**
Lo decidimos con ustedes. Nuestra propuesta es dejar al final la captura sin señal, porque el escaneo ya funciona con conexión. La pantalla única y los apartados por rol van primero porque fueron sus pedidos principales.

### Bloqueo por comprobaciones vencidas (@juanpismata11)

_Pendiente: al menos dos preguntas con su respuesta, por pull request._

### Escaneo rápido y comprobante válido (@PauAlba)

_Pendiente: al menos dos preguntas con su respuesta, por pull request._

### Saldos y pantalla única (@jaaaaaaaaasiel)

_Pendiente: al menos dos preguntas con su respuesta, por pull request._

### Apartados por rol (@casizzy)

_Pendiente: al menos dos preguntas con su respuesta, por pull request._

## 7. Preguntas que quedaron sin respuesta

Se llena durante la presentación. Cada pregunta se contesta al cliente por Slack.

| Pregunta | Quién la responde | Fecha de respuesta por Slack |
| :--- | :--- | :--- |
| | | |

## 8. Preparación y respaldo

- [ ] La release v0.3.0 está publicada con su paquete y su archivo SHA-256.
- [ ] La aplicación está instalada desde ese paquete en la computadora y el celular que se usan, con los datos de ejemplo recién cargados.
- [ ] Están listas las tres diapositivas: objetivo y compromiso, planeado contra terminado, manejo de propuestas.
- [ ] Hay un video corto de la demostración, grabado con el mismo paquete, guardado sin depender de internet.
- [ ] Se ensayó con cronómetro al menos una vez. Duración del ensayo: ____ min.

## 9. Retrospectiva

Se llena después de la presentación.

### Qué funcionó

-

### Qué no funcionó

-

### Qué cambia el equipo en la presentación con el cliente real

| # | Cambio | Responsable |
| :--- | :--- | :--- |
| 1 | | |
