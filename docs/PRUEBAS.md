# Pruebas y calidad del software

Este documento explica cómo se prueba el proyecto, qué revisa el flujo de GitHub Actions en cada pull request y qué umbrales acordó el equipo. La investigación que respalda cada decisión está en el issue del Project *Investigación: pruebas y calidad del software*.

## Cómo ejecutar todo en tu computadora

Con el entorno virtual activado y las dependencias instaladas (`pip install -r requirements.txt`), desde la raíz del repositorio:

```bash
ruff check .                 # análisis estático (linter y complejidad)
python -m pytest tests -v    # pruebas automatizadas
```

Si los dos comandos terminan sin errores en tu computadora, el flujo de GitHub Actions también debe quedar en verde.

## Flujo de GitHub Actions

El archivo `.github/workflows/calidad.yml` corre en cada pull request hacia `main` y en cada push a `main`. Si cualquier paso falla, el pull request muestra la verificación **Calidad / Linter y pruebas** en rojo y no debe integrarse hasta que quede en verde.

| Paso | Herramienta | Falla cuando |
| --- | --- | --- |
| Linter | Ruff | Hay cualquier hallazgo, incluida una función con complejidad mayor a 10 |
| Pruebas | pytest | Alguna prueba falla |

Fuentes: [GitHub Actions · Compilar y probar Python](https://docs.github.com/es/actions/tutorials/build-and-test-code/python), [GitHub · Verificaciones de estado](https://docs.github.com/es/pull-requests/reference/status-checks).

---

## 1. Análisis estático

### Linter: Ruff

Usamos [Ruff](https://docs.astral.sh/ruff/) porque es el linter de Python indicado para el proyecto y se configura en un solo archivo, `pyproject.toml`. La versión está fijada en `requirements.txt` (`ruff==0.17.6`) para que todos y el flujo corran exactamente las mismas reglas.

Reglas activadas (`[tool.ruff.lint]` en `pyproject.toml`):

| Código | Qué detecta |
| --- | --- |
| `E4`, `E7`, `E9` | Imports mal ubicados, comparaciones incorrectas y errores de sintaxis |
| `F` (Pyflakes) | Imports y variables sin usar, nombres no definidos |
| `C901` | Funciones con complejidad ciclomática mayor al máximo |

**Regla de complejidad.** Ruff no trae `C901` activada por defecto. Se activa agregándola a `select` y se ajusta con `max-complexity` en `[tool.ruff.lint.mccabe]`, cuyo valor por defecto es 10. La complejidad ciclomática cuenta los caminos independientes de una función: cada `if`, `elif`, `for`, `while`, `except`, `and` u `or` suma uno.

```toml
[tool.ruff.lint]
select = ["E4", "E7", "E9", "F", "C901"]

[tool.ruff.lint.mccabe]
max-complexity = 10
```

Fuentes: [Ruff · Selección de reglas](https://docs.astral.sh/ruff/linter/#rule-selection), [Ruff · Regla C901](https://docs.astral.sh/ruff/rules/complex-structure/), [Ruff · max-complexity](https://docs.astral.sh/ruff/settings/#lint_mccabe_max-complexity), [Ruff · GitHub Actions](https://docs.astral.sh/ruff/integrations/#github-actions), [OWASP · Static Code Analysis](https://owasp.org/www-community/controls/Static_Code_Analysis).

### Cobertura

<!-- Pendiente: Juan Pablo. Herramienta, comando para generar el reporte y cómo se configura el umbral que hace fallar el flujo. -->

### Umbrales acordados

| Umbral | Valor | Por qué |
| --- | --- | --- |
| Complejidad ciclomática máxima por función (`C901`) | 10 | Es el valor por defecto de Ruff y el límite original de McCabe. Con el código actual solo una función lo superaba, así que el límite es exigente sin obligar a reescribir el proyecto. |
| Hallazgos del linter permitidos | 0 | El código actual quedó sin hallazgos; cualquier hallazgo nuevo pone el flujo en rojo. |
| Cobertura mínima | <!-- Pendiente: Juan Pablo --> | <!-- Pendiente: Juan Pablo --> |

### Resultado del primer análisis

Se corrió Ruff 0.17.6 sobre `src/` y `tests/` antes de corregir nada (rama `chore/analisis-estatico-ruff`, a partir de `main` en el commit `728a3ef`).

**Con la configuración por defecto de Ruff 0.17.6 (sin `pyproject.toml`): 143 hallazgos**, de los cuales Ruff puede corregir 123 en automático. Casi todos son de estilo y modernización de código, no errores:

| Código | Regla | Hallazgos |
| --- | --- | --- |
| `UP045` | Usar `X \| None` en lugar de `Optional[X]` | 62 |
| `UP006` | Usar `list` y `dict` en lugar de `List` y `Dict` | 21 |
| `I001` | Imports sin ordenar | 15 |
| `UP035` | Import obsoleto de `typing` | 14 |
| `UP017` | Usar `datetime.UTC` | 10 |
| `FURB157` | `Decimal` construido de forma redundante | 8 |
| Otras 6 reglas | `B008`, `RET501`, `PLR1711`, `DTZ003`, `RUF012`, `F401` | 13 |

**Con las reglas acordadas por el equipo: 2 hallazgos**, los dos corregidos en la misma rama:

| Archivo | Hallazgo | Corrección |
| --- | --- | --- |
| `tests/test_hu01_solicitud.py:9` | `F401`: `uuid.UUID` importado y sin usar | Se eliminó el import |
| `src/services/saldo_service.py:65` | `C901`: `por_obra` con complejidad 12 (máximo 10) | Se separó en `_sumar_solicitudes`, `_sumar_comprobantes` y `calcular_indicadores`; ahora la más compleja tiene 5. Las pruebas de saldos siguen pasando y se agregó `tests/test_saldo_indicadores.py` |

**Por qué no adoptamos el conjunto por defecto completo.** Corregir los 143 hallazgos tocaría casi todos los archivos del proyecto al mismo tiempo que los demás integrantes trabajan en sus ramas, y la mayoría son cambios de estilo que no evitan errores. Empezamos con las reglas que sí detectan errores más la de complejidad; ampliar la selección (por ejemplo `I` para ordenar imports o `UP` para modernizar anotaciones) queda como propuesta para un pull request propio.

---

## 2. Pruebas de seguridad

### Validación de entradas del usuario

<!-- Pendiente: Paulina. Dónde y cómo se validan las entradas, qué entrada se validó y qué prueba comprueba el caso que debe fallar. -->

### Dependencias con vulnerabilidades conocidas

<!-- Pendiente: Jaasiel. Herramienta disponible en el plan de la organización, cómo se ejecuta en el flujo y qué se hace cuando reporta algo. -->

### Secretos: búsqueda y resguardo

<!-- Pendiente: Stella. Cómo se buscan llaves y contraseñas en el código y en el historial, dónde se guardan los secretos y qué se hace si aparece uno. -->
