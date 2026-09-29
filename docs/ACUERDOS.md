# Acuerdos del equipo

## Acuerdo número 1
Mensajes de commit estructurados: adoptar Conventional Commits (`<tipo>(<alcance>): <descripción>`) para facilitar la lectura del historial del proyecto.

## Acuerdo número 2
Gestión de secretos y seguridad: está estrictamente prohibido subir archivos `.env`, contraseñas o tokens al repositorio. Cualquier configuración de entorno requerida debe documentarse únicamente en un archivo `.env.example`.

## Acuerdo número 3
Nomenclatura de ramas: establecer un estándar estricto para crear ramas, como `feat/nombre-tarea`, `fix/bug-detectado` o `hotfix/error-urgente`. Esto mantiene el repositorio organizado cuando los 5 integrantes trabajan en paralelo.

## Acuerdo número 4
Asignación de tareas: para evitar duplicidad de trabajo, nadie debe comenzar a programar una funcionalidad sin antes haberse asignado explícitamente el issue o la tarea en el tablero del proyecto.

## Acuerdo número 5
Definición de Terminado (DoD): una tarea solo se considera terminada cuando cumple todos los criterios de la sección [Definición de Terminado](#definición-de-terminado-dod) de este documento.

## Acuerdo número 6
Regla de bloqueos de 24 horas: si un integrante lleva más de un día atascado en un problema técnico o de lógica de negocio, tiene la obligación de pedir ayuda al equipo.

## Acuerdo número 7
Estimación y prioridad: los requerimientos y las historias de usuario se estiman en **horas** con la misma escala (2, 4, 8, 12, 16, 24). La estimación de un requerimiento es la suma de las historias que lo componen. La prioridad se expresa como Alta, Media o Baja; una historia hereda la prioridad de su requerimiento.

---

# Definición de Terminado (DoD)

Una tarea del tablero (requerimiento o historia de usuario) solo puede moverse al estado **Done** (Terminado) cuando cumple **todos** los criterios aplicables.

## 1. Criterios generales (toda tarea)
- [ ] La tarea tiene título, descripción, iteración, estimación en horas, prioridad y estado en el tablero.
- [ ] La tarea está asignada a al menos un integrante del equipo.
- [ ] El trabajo se realizó en una rama con la nomenclatura acordada (`feat/`, `fix/`, `hotfix/`).
- [ ] Los commits siguen Conventional Commits y referencian el issue (`#<número>`).
- [ ] Existe un Pull Request con Resumen, Tipo de cambio, Verificación e Issue vinculado (`Closes #<número>`).
- [ ] El Pull Request fue revisado y aprobado por al menos un integrante distinto al autor.
- [ ] Los archivos respetan `.editorconfig`: indentación con espacios, UTF-8 sin BOM, fin de línea LF y salto de línea final.
- [ ] No se incluyen secretos, credenciales ni archivos `.env` en el repositorio.
- [ ] El código compila/ejecuta sin errores y no rompe el flujo existente de administración de gastos.
- [ ] Los cambios están integrados en la rama `main`.

## 2. Historias de usuario
- [ ] Se cumplen **todos** los criterios de aceptación (Dado / Cuando / Entonces) de la historia.
- [ ] Cada criterio de aceptación fue verificado con una prueba (automatizada o manual documentada en el PR).
- [ ] El comportamiento fue demostrado al equipo (o al cliente) y aceptado.
- [ ] La documentación afectada (`docs/HISTORIAS.md`, `README.md`) está actualizada.

## 3. Requerimientos funcionales (RF)
- [ ] Todas las historias de usuario asociadas al requerimiento están en estado **Done**.
- [ ] Se respetan las reglas de negocio de caja chica:
  - No existen borrados físicos (*hard delete*) en solicitudes, gastos o comprobantes; solo borrado lógico (*soft delete*).
  - Un gasto con estado `Aprobado` o `Conciliado` no puede modificar sus montos ni detalles.
  - Las correcciones a gastos aprobados se registran como un nuevo movimiento de "Reverso" o "Ajuste" que referencia el UUID del original.
- [ ] Las acciones relevantes (autorización, entrega, comprobación, conciliación) quedan registradas con usuario y fecha para auditoría.

## 4. Requerimientos no funcionales (RNF)
- [ ] El indicador definido en `docs/REQUERIMIENTOS.md` fue medido y cumple la meta establecida.
- [ ] La evidencia de la medición (capturas, tiempos, resultados de importación) está adjunta en el PR o en el issue.
- [ ] Todas las historias de usuario asociadas al requerimiento están en estado **Done**.

## 5. Estados del tablero
| Estado | Significado |
| :--- | :--- |
| **Todo** (Pendiente, estado inicial) | La tarea está en el backlog, priorizada y estimada, pero nadie trabaja en ella. |
| **In Progress** (En progreso) | Un integrante se la asignó y está trabajando en ella, o su Pull Request está en revisión. |
| **Done** (Terminado) | Cumple todos los criterios de esta Definición de Terminado. |
