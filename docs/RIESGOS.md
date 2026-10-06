
=======
# Registro de Riesgos

> Cada riesgo indica su causa y la consecuencia que tendría sobre la aplicación.
> Probabilidad e impacto se califican como Baja/Media/Alta; la respuesta indica la estrategia (Evitar, Reducir, Transferir o Aceptar) y la acción concreta.

| ID | Riesgo | Probabilidad | Impacto | Respuesta | Responsable |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **R-01** | Los comprobantes que se fotografían en obra son notas simples escritas a mano, así que la extracción automática devuelve montos o proveedores incorrectos y la conciliación marca diferencias falsas. | Alta | Alto | *Reducir:* Mostrar los datos extraídos para que el usuario los confirme o corrija antes de guardar. | MATA AGUIRRE, JUAN PABLO (80446) |
| **R-02** | Los requerimientos de flujos de aprobación de gastos cambian durante las demostraciones del producto, causando retrasos en las entregas planificadas. | Alta | Media | *Aceptar:* Bajar el alcance del ciclo actual y redefinir los entregables clave para la siguiente demostración. | JARA VILLASANA, MARIANO (80547) |
| *R-03* | El fondo de caja chica no se repone a tiempo por demoras en las aprobaciones, dejando a los colaboradores sin liquidez para operativos inmediatos. | Alta | Media | *Aceptar:* Establecer alertas automáticas de nivel crítico al llegar al 20% del fondo y habilitar un flujo de aprobación de emergencia. | CASILLAS RAMÍREZ, STELLA ISABEL (38919) |
| *R-04* | El módulo de contabilidad/ERP cambia sus parámetros de integración a mitad del proyecto, interrumpiendo la sincronización de asientos contables. | Baja | Alto | *Transferir:* Aislar la integración mediante un servicio middleware o adaptador que transforme la data antes de ser enviada al ERP. | OROZCO DE ALBA, PAULINA (79849) |
