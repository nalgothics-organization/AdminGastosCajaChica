# Acuerdos del equipo

## Acuerdo número 1
**Mensajes de commit estructurados:** Adoptar Conventional Commits (`<tipo>(<alcance>): <descripción>`) para facilitar la lectura del historial del proyecto.

## Acuerdo número 2
**Gestión de secretos y seguridad:** Está estrictamente prohibido subir archivos `.env`, contraseñas o tokens al repositorio. Cualquier configuración de entorno requerida debe documentarse únicamente en un archivo `.env.example`.

## Acuerdo número 3
**Nomenclatura de ramas (Conventional Commits):** Las ramas se nombran `<tipo>/<descripcion-corta>`, usando como tipo los de la especificación https://www.conventionalcommits.org/en/v1.0.0/:

- `feat/` nueva funcionalidad
- `fix/` corrección de un error
- `docs/` solo documentación
- `style/` formato, sin cambios de lógica
- `refactor/` reestructura de código sin cambiar su comportamiento
- `test/` pruebas
- `chore/` mantenimiento, configuración o versiones

La descripción va en minúsculas, con palabras separadas por guiones, sin acentos, sin espacios ni la letra ñ, y puede empezar con el número de issue. Ejemplos: `feat/42-captura-rapida`, `fix/saldo-negativo`, `docs/plantilla-pr`. El tipo de la rama debe coincidir con el tipo de los commits que contiene (Acuerdo 1).

## Acuerdo número 4
**Asignación de tareas:** Para evitar duplicidad de trabajo, nadie debe comenzar una tarea sin antes haberse asignado explícitamente el Issue o la tarjeta en el tablero del proyecto.

## Acuerdo número 5
**Regla de bloqueos de 24 horas:** Si un integrante lleva más de un día atascado en un problema técnico o de lógica de negocio, tiene la obligación de avisar y pedir ayuda al equipo.

## Acuerdo número 6
**Estimación y priorización:** Requerimientos e historias de usuario se estiman en **horas**, con la misma escala para ambos tipos de tarea. La estimación de un requerimiento es la suma de las estimaciones de sus historias de usuario (sub-issues). La prioridad se expresa como Alta, Media o Baja. El backlog se ordena por identificador numérico (RF, RNF y HU) y por iteración.

## Acuerdo número 7
**Rama principal con revisión obligatoria:** La rama principal del proyecto es `main`. Nadie hace push directo a `main`. Todo cambio entra mediante Pull Request y requiere al menos 1 aprobación de un integrante distinto al autor antes de fusionarse. Si se agregan commits nuevos al PR, la aprobación se vuelve asolicitar. Esta regla está configurada como protección de rama en GitHub (Settings → Branches) y aplica también a los administradores.

## Acuerdo número 8
**Borrado de ramas al fusionar:** Cuando un Pull Request se fusiona a `main`, su rama se elimina del repositorio remoto; GitHub lo hace automáticamente con la opción "Automatically delete head branches". El autor también borra su copia local con `git branch -d <rama>` y limpia las referencias con `git fetch --prune`. Una rama fusionada no se reutiliza: cualquier cambio posterior se hace en una rama nueva creada desde `main` actualizada.
---

# Definición de Terminado (DoD)

Una tarea del tablero solo puede moverse al estado **Terminado** cuando cumple **todos** los criterios que le aplican. Si falta alguno, la tarea permanece en su estado actual.

## Criterios generales (aplican a toda tarea)

1. La tarjeta tiene título, descripción, iteración, estimación en horas, prioridad y estado.
2. La tarea está asignada a un responsable (Acuerdo 4).
3. El trabajo se desarrolló en una rama con la nomenclatura acordada (Acuerdo 3) y se integró a `main` mediante Pull Request.
4. El Pull Request incluye resumen, tipo de cambio, pasos de verificación y referencia al Issue (`Closes #<número>`).
5. El Pull Request fue revisado y aprobado por al menos **un** integrante distinto al autor.
6. Los commits siguen Conventional Commits (Acuerdo 1).
7. Los archivos respetan `.editorconfig`: UTF-8 sin BOM, finales de línea LF, sangría con espacios y salto de línea final.
8. No se incluyen secretos, credenciales ni archivos `.env` (Acuerdo 2).
9. El código compila / se ejecuta sin errores y no rompe el flujo existente de administración de gastos.
10. Se registraron en la tarjeta las horas reales invertidas.

## Requerimiento funcional (RF)

1. Todas las historias de usuario ligadas al requerimiento están en **Terminado**.
2. La funcionalidad descrita en el catálogo (`docs/REQUERIMIENTOS.md`) está implementada completa.
3. Se respetan las reglas de negocio de caja chica:
   - No existen borrados físicos en transacciones, gastos o comprobantes; solo borrado lógico.
   - Un gasto `Aprobado` o `Conciliado` no puede modificarse; las correcciones se hacen con un registro de **Reverso** o **Ajuste** que referencia el UUID original.
4. Se verificó el requerimiento de extremo a extremo (captura → autorización → comprobación, según aplique).

## Requerimiento no funcional (RNF)

1. El indicador definido en el catálogo se midió y cumple con la meta establecida (por ejemplo: máximo 3 toques para capturar un ticket; sincronización offline en menos de 60 segundos).
2. La evidencia de la medición (capturas, tiempos, bitácora de prueba) está adjunta a la tarjeta o al Pull Request.
3. Sus historias de usuario asociadas están en **Terminado**.

## Historia de usuario (HU)

1. Todos los criterios de aceptación (Dado / Cuando / Entonces) se probaron y se cumplen.
2. Existen pruebas (automatizadas o manuales documentadas) que cubren cada criterio de aceptación.
3. El rol de la historia (residente de obra, administración, contabilidad o dirección) puede completar el flujo sin ayuda del equipo de desarrollo.
4. La historia fue demostrada al equipo y validada por el responsable de producto.

## Documentación

1. Si la tarea cambió el alcance, se actualizaron `docs/REQUERIMIENTOS.md` y `docs/HISTORIAS.md`.
2. Los cambios de configuración o de entorno quedaron documentados en `README.md` o en `.env.example`.
