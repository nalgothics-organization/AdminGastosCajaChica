"""Pruebas del resguardo de secretos (Acuerdo 2 y docs/PRUEBAS.md).

Comprueban que el archivo .env nunca entre al repositorio y que .env.example solo traiga
valores de ejemplo, no contraseñas reales.
"""

import os
import subprocess
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
VARIABLES_SECRETAS = ("SECRET_KEY", "POSTGRES_PASSWORD")


def leer_variables(nombre_archivo):
    variables = {}
    with open(os.path.join(RAIZ, nombre_archivo), encoding="utf-8") as archivo:
        for linea in archivo:
            linea = linea.strip()
            if linea and not linea.startswith("#") and "=" in linea:
                clave, valor = linea.split("=", 1)
                variables[clave.strip()] = valor.strip()
    return variables


class TestSecretos(unittest.TestCase):
    def test_env_esta_en_gitignore(self):
        with open(os.path.join(RAIZ, ".gitignore"), encoding="utf-8") as archivo:
            reglas = [linea.strip() for linea in archivo]

        self.assertIn(".env", reglas)

    def test_env_no_esta_versionado(self):
        versionados = subprocess.run(
            ["git", "ls-files", ".env"], cwd=RAIZ, capture_output=True, text=True, check=True
        ).stdout

        self.assertEqual(versionados.strip(), "")

    def test_env_example_solo_trae_valores_de_ejemplo(self):
        variables = leer_variables(".env.example")

        for clave in VARIABLES_SECRETAS:
            with self.subTest(variable=clave):
                self.assertTrue(variables[clave].startswith("change_this"), f"{clave} parece un valor real")


if __name__ == "__main__":
    unittest.main()
