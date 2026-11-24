"""
Pruebas de las dependencias declaradas en requirements.txt.

pip-audit revisa las versiones que resultan de requirements.txt. Estas pruebas cuidan que cada
dependencia tenga versión declarada y que las herramientas del flujo estén fijadas a una versión exacta.

"""

import os
import re
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
REQUIREMENTS = os.path.join(RAIZ, "requirements.txt")
LINEA_CON_VERSION = re.compile(r"^[A-Za-z0-9_.\-\[\]]+\s*(==|>=|~=)\s*\d")


def leer_dependencias():
    with open(REQUIREMENTS, encoding="utf-8") as archivo:
        lineas = [linea.strip() for linea in archivo]
    return [linea for linea in lineas if linea and not linea.startswith("#")]


class TestDependencias(unittest.TestCase):
    def test_todas_las_dependencias_declaran_version(self):
        sin_version = [d for d in leer_dependencias() if not LINEA_CON_VERSION.match(d)]

        self.assertEqual(sin_version, [], f"Dependencias sin versión: {sin_version}")

    def test_las_herramientas_del_flujo_estan_fijadas(self):
        dependencias = leer_dependencias()

        for herramienta in ("ruff", "pip-audit"):
            with self.subTest(herramienta=herramienta):
                fijadas = [d for d in dependencias if re.match(rf"^{herramienta}==\d", d)]
                self.assertEqual(len(fijadas), 1, f"{herramienta} debe aparecer una vez con '=='")

    def test_no_hay_dependencias_repetidas(self):
        nombres = [re.split(r"[=<>~\[ ]", d, maxsplit=1)[0].lower() for d in leer_dependencias()]

        self.assertEqual(len(nombres), len(set(nombres)))


if __name__ == "__main__":
    unittest.main()
