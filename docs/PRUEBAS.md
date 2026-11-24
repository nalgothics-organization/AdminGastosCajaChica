# Pruebas y calidad del software

Este documento explica cómo se prueba el proyecto, qué revisa el flujo de GitHub Actions en cada pull request y qué umbrales acordó el equipo. La investigación que respalda cada decisión está en el issue del Project *Investigación: pruebas y calidad del software*.

## Cómo ejecutar todo en tu computadora

Con el entorno virtual activado y las dependencias instaladas (`pip install -r requirements.txt`), desde la raíz del repositorio:

```bash
ruff check .                 # análisis estático (linter y complejidad)
python -m pytest tests -v --cov --cov-report=term-missing   # pruebas y cobertura
pip-audit -r requirements.txt   # dependencias con vulnerabilidades conocidas
```

Si los dos comandos terminan sin errores en tu computadora, el flujo de GitHub Actions también debe quedar en verde.

## Flujo de GitHub Actions

El archivo `.github/workflows/calidad.yml` corre en cada pull request hacia `main` y en cada push a `main`. Si cualquier paso falla, el pull request muestra la verificación **Calidad / Linter y pruebas** en rojo y no debe integrarse hasta que quede en verde.

| Paso | Herramienta | Falla cuando |
| --- | --- | --- |
| Linter | Ruff | Hay cualquier hallazgo, incluida una función con complejidad mayor a 10 |
| Pruebas y cobertura | pytest + pytest-cov | Alguna prueba falla o la cobertura de `src/` baja de 90 % |
| Dependencias | pip-audit | Alguna dependencia de `requirements.txt` tiene una vulnerabilidad conocida |

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

Medimos la cobertura con [coverage.py](https://coverage.readthedocs.io/) a través del plugin [pytest-cov](https://pytest-cov.readthedocs.io/), fijado en `requirements.txt` (`pytest-cov==7.1.0`).

```bash
python -m pytest tests --cov --cov-report=term-missing
```

`--cov` toma la carpeta a medir de `[tool.coverage.run] source = ["src"]` y `--cov-report=term-missing` imprime el porcentaje por archivo y las líneas que ninguna prueba ejecutó. El umbral está en `pyproject.toml`:

```toml
[tool.coverage.report]
fail_under = 90
```

Si la cobertura total queda por debajo de 90 %, pytest termina con el mensaje `FAIL Required test coverage of 90% not reached` y el paso del flujo falla.

Medición al configurarla: 95 % de `src/`. El archivo más bajo era `src/api/obras.py` (50 %); con `tests/test_api_obras.py` llegó a 100 % y el total quedó en 96 %.

Fuentes: [pytest-cov · Configuración](https://pytest-cov.readthedocs.io/en/latest/config.html), [coverage.py · fail_under](https://coverage.readthedocs.io/en/latest/config.html#report-fail-under).

### Umbrales acordados

| Umbral | Valor | Por qué |
| --- | --- | --- |
| Complejidad ciclomática máxima por función (`C901`) | 10 | Es el valor por defecto de Ruff y el límite original de McCabe. Con el código actual solo una función lo superaba, así que el límite es exigente sin obligar a reescribir el proyecto. |
| Hallazgos del linter permitidos | 0 | El código actual quedó sin hallazgos; cualquier hallazgo nuevo pone el flujo en rojo. |
| Cobertura mínima de `src/` (`fail_under`) | 90 % | La cobertura actual es 96 %. Dejar 6 puntos de margen permite agregar código, pero un PR con mucho código sin pruebas pone el flujo en rojo. |

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

Validamos en el servidor, en los modelos de Pydantic, antes de que el dato llegue a la base de datos o a la pantalla de otro usuario. Si un `field_validator` lanza `ValueError`, la API responde **422** y no guarda nada. Seguimos la recomendación de OWASP de usar **lista de permitidos**: se define exactamente qué formato se acepta y todo lo demás se rechaza.

**Entrada validada: `evidencia_url` de la solicitud de fondo.** Antes aceptaba cualquier texto, así que se podía guardar `javascript:alert(1)` o `/api/evidencias/../../.env` y mostrárselo a quien autoriza. Ahora solo acepta:

| Formato permitido | Ejemplo |
| --- | --- |
| Foto subida a la API: `/api/evidencias/<uuid>.jpg` (también `.png` o `.webp`) | `/api/evidencias/0b8f6c2e-1d4a-4f6b-9c3e-5a7d2e9f1b04.jpg` |
| Enlace `http://` o `https://` sin espacios, `<`, `>` ni comillas | `https://storage.empresa.com/evidencias/fuga.jpg` |

**Casos que deben fallar** (`tests/test_validacion_evidencia.py`): un enlace `javascript:`, una ruta con `../` y un enlace con HTML incrustado responden 422 con el mensaje de error, y la solicitud no se guarda.

Otras validaciones que ya existían: montos mayores a cero (`gt=0`), partidas genéricas prohibidas, obra obligatoria, y fotos revisadas por su firma de bytes y tamaño (`validar_imagen`). Las consultas usan SQLAlchemy con parámetros, lo que evita la inyección SQL.

Fuentes: [OWASP · Input Validation Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Input_Validation_Cheat_Sheet.html), [OWASP Top 10](https://top10.owasp.org/es/).

### Dependencias con vulnerabilidades conocidas

La organización está en el plan GitHub Free y el repositorio es público. Usamos dos herramientas que se complementan:

| Herramienta | Cuándo actúa | Qué hace |
| --- | --- | --- |
| [pip-audit](https://pypi.org/project/pip-audit/) | En cada pull request (paso *Revisión de dependencias*) | Revisa `requirements.txt` contra la base de vulnerabilidades de Python. Termina con código 1 si encuentra algo y el flujo se marca en rojo |
| [Dependabot alerts](https://docs.github.com/es/code-security/concepts/supply-chain-security/dependabot-alerts) | Siempre, aunque nadie abra un PR | Avisa en la pestaña *Security* cuando una versión que ya usamos tiene una vulnerabilidad nueva. `.github/dependabot.yml` además abre cada semana PRs para actualizar versiones |

Resultado del primer análisis: `pip-audit -r requirements.txt` → `No known vulnerabilities found`.

**Si aparece una vulnerabilidad:** se sube la versión del paquete en `requirements.txt` a una que la corrija, en un PR `fix(deps)`. Si no existe corrección y el riesgo no aplica al proyecto, se puede ignorar con `pip-audit --ignore-vuln <ID>`, dejando escrito el motivo en el PR.

Fuentes: [pip-audit](https://pypi.org/project/pip-audit/), [GitHub · Alertas de Dependabot](https://docs.github.com/es/code-security/concepts/supply-chain-security/dependabot-alerts), [GitHub · Planes](https://docs.github.com/es/get-started/learning-about-github/githubs-plans).

### Secretos: búsqueda y resguardo

<!-- Pendiente: Stella. Cómo se buscan llaves y contraseñas en el código y en el historial, dónde se guardan los secretos y qué se hace si aparece uno. -->
