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
| Secretos (job aparte) | Gitleaks | Aparece una llave, token o contraseña en los archivos o en cualquier commit del historial |

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

<!-- Pendiente: Paulina. Dónde y cómo se validan las entradas, qué entrada se validó y qué prueba comprueba el caso que debe fallar. -->

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

**Búsqueda en código e historial.** El job *Búsqueda de secretos* del flujo descarga todo el historial (`fetch-depth: 0`) y corre [Gitleaks](https://github.com/gitleaks/gitleaks) sobre cada commit. Si encuentra una llave o contraseña, termina con código 1 y el PR se marca en rojo. Usamos la imagen oficial de Docker porque la acción `gitleaks-action` pide licencia en repositorios de organizaciones.

Para correrlo en tu computadora:

```bash
gitleaks git -v --redact .    # todo el historial
gitleaks dir -v --redact .    # archivos actuales
```

Resultado del primer análisis: **0 hallazgos** en el historial completo.

Además, como el repositorio es público, están activados sin costo **secret scanning** (GitHub avisa si detecta un secreto conocido) y **push protection** (bloquea el push que trae un secreto).

**Dónde se guardan los secretos:**

| Dónde | Qué va ahí |
| --- | --- |
| `.env` en tu computadora (en `.gitignore`, nunca se sube) | Contraseña de PostgreSQL, `SECRET_KEY` y cualquier valor real |
| `.env.example` en el repo | Solo los nombres de las variables con valores de ejemplo (`change_this_...`) |
| GitHub → Settings → Secrets and variables → Actions | Secretos que necesite el flujo; se leen con `${{ secrets.NOMBRE }}` y GitHub los oculta en los logs |

`tests/test_secretos.py` comprueba que `.env` esté en `.gitignore`, que no esté versionado y que `.env.example` solo traiga valores de ejemplo.

**Si aparece un secreto:**

1. Avisar al equipo en ese momento.
2. **Revocar y cambiar** la llave o contraseña donde se generó. Borrarla del archivo no basta: sigue en el historial y cualquiera que haya clonado el repo la tiene.
3. Quitarla del código, moverla a `.env` o a GitHub Secrets y abrir un PR `fix(security)` que lo explique.
4. Si es un falso positivo (un valor de ejemplo), agregar su fingerprint a `.gitleaksignore` y explicarlo en el PR.

Fuentes: [Gitleaks](https://github.com/gitleaks/gitleaks), [OWASP · Secrets Management Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/Secrets_Management_Cheat_Sheet.html), [GitHub Actions · Uso de secretos](https://docs.github.com/es/actions/how-tos/write-workflows/choose-what-workflows-do/use-secrets), [GitHub · Secret scanning](https://docs.github.com/es/code-security/secret-scanning/introduction/about-secret-scanning).
