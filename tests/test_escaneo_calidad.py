"""Pruebas de la revisión de calidad de la foto del escaneo (RNF05/HU21).

La revisión corre en el navegador (src/static/calidad.js); aquí se ejecuta con Node sobre imágenes
sintéticas para comprobar que una foto borrosa u oscura se detecta y una nítida y clara no.
"""

import json
import os
import shutil
import subprocess
import unittest

RAIZ = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
CALIDAD_JS = os.path.join(RAIZ, "src", "static", "calidad.js")

# Genera cada imagen RGBA de 64x64 y devuelve el resultado de evaluarCalidad como JSON
SCRIPT_NODE = """
const { evaluarCalidad } = require(process.argv[1]);
const LADO = 64;

function imagen(valorEn) {
  const pixeles = new Uint8ClampedArray(LADO * LADO * 4);
  for (let y = 0; y < LADO; y++) {
    for (let x = 0; x < LADO; x++) {
      const valor = valorEn(x, y);
      pixeles.set([valor, valor, valor, 255], (y * LADO + x) * 4);
    }
  }
  return pixeles;
}

const tablero = (oscuro, claro) => (x, y) => ((x >> 2) + (y >> 2)) % 2 === 0 ? oscuro : claro;
const casos = {
  nitida: tablero(30, 220),
  borrosa: (x) => 80 + x,
  oscura: tablero(0, 40),
  oscura_y_borrosa: () => 10,
};

const resultado = {};
for (const [nombre, valorEn] of Object.entries(casos)) {
  resultado[nombre] = evaluarCalidad(imagen(valorEn), LADO, LADO);
}
console.log(JSON.stringify(resultado));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js no está instalado")
class TestCalidadFoto(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        salida = subprocess.run(
            ["node", "-e", SCRIPT_NODE, CALIDAD_JS], capture_output=True, text=True, check=True
        ).stdout
        cls.resultado = json.loads(salida)

    def test_foto_nitida_y_clara_se_acepta(self):
        self.assertEqual(self.resultado["nitida"], {"oscura": False, "borrosa": False})

    def test_foto_borrosa_pide_repetirse(self):
        self.assertEqual(self.resultado["borrosa"], {"oscura": False, "borrosa": True})

    def test_foto_oscura_pide_repetirse(self):
        self.assertEqual(self.resultado["oscura"], {"oscura": True, "borrosa": False})

    def test_foto_oscura_y_borrosa_se_detectan_las_dos(self):
        self.assertEqual(self.resultado["oscura_y_borrosa"], {"oscura": True, "borrosa": True})


if __name__ == "__main__":
    unittest.main()
