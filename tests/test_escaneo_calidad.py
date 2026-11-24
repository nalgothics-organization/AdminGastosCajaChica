"""Pruebas del aviso de foto oscura del escaneo (RNF05/HU21).

La revisión corre en el navegador (src/static/calidad.js); aquí se ejecuta con Node sobre imágenes
sintéticas. La nitidez y el contenido se revisan en el servidor con OCR (tests/test_legibilidad.py).
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
  clara: tablero(30, 220),
  oscura: tablero(0, 40),
  negra: () => 10,
};

const resultado = {};
for (const [nombre, valorEn] of Object.entries(casos)) {
  resultado[nombre] = evaluarCalidad(imagen(valorEn), LADO, LADO);
}
console.log(JSON.stringify(resultado));
"""


@unittest.skipUnless(shutil.which("node"), "Node.js no está instalado")
class TestFotoOscura(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        salida = subprocess.run(
            ["node", "-e", SCRIPT_NODE, CALIDAD_JS], capture_output=True, text=True, check=True
        ).stdout
        cls.resultado = json.loads(salida)

    def test_foto_con_buena_luz_se_acepta(self):
        self.assertEqual(self.resultado["clara"], {"oscura": False})

    def test_foto_oscura_pide_repetirse(self):
        self.assertEqual(self.resultado["oscura"], {"oscura": True})

    def test_foto_casi_negra_pide_repetirse(self):
        self.assertEqual(self.resultado["negra"], {"oscura": True})


if __name__ == "__main__":
    unittest.main()
