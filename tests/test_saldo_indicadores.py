"""Pruebas de los indicadores del saldo por obra (RF10/HU10).

Cubren SaldoService.calcular_indicadores, que se separó de por_obra para cumplir
la regla de complejidad C901 (máximo 10) acordada en docs/PRUEBAS.md.
"""

import os
import sys
import unittest
from decimal import Decimal

# Asegurar que la raíz del proyecto esté en el PYTHONPATH al ejecutar el script directamente
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from src.services.saldo_service import SaldoObra, SaldoService


def saldo(presupuesto="0", autorizado="0", comprobado="0"):
    return SaldoObra(
        obra_id="OBRA-PRUEBA",
        presupuesto_caja_chica=Decimal(presupuesto),
        autorizado=Decimal(autorizado),
        comprobado=Decimal(comprobado),
    )


class TestCalcularIndicadores(unittest.TestCase):
    def test_calcula_disponible_por_comprobar_y_porcentajes(self):
        resultado = SaldoService.calcular_indicadores(saldo("20000.00", "3500.00", "3200.00"))

        self.assertEqual(resultado.disponible_caja_chica, Decimal("16500.00"))
        self.assertEqual(resultado.por_comprobar, Decimal("300.00"))
        self.assertEqual(resultado.porcentaje_autorizado, Decimal("17.5"))
        self.assertEqual(resultado.porcentaje_gastado, Decimal("91.4"))

    def test_sin_fondo_ni_autorizado_no_divide_entre_cero(self):
        resultado = SaldoService.calcular_indicadores(saldo())

        self.assertEqual(resultado.porcentaje_autorizado, Decimal("0"))
        self.assertEqual(resultado.porcentaje_gastado, Decimal("0"))
        self.assertEqual(resultado.disponible_caja_chica, Decimal("0"))

    def test_autorizar_mas_que_el_fondo_deja_disponible_negativo(self):
        resultado = SaldoService.calcular_indicadores(saldo("1000.00", "1500.00"))

        self.assertEqual(resultado.disponible_caja_chica, Decimal("-500.00"))
        self.assertEqual(resultado.porcentaje_autorizado, Decimal("150.0"))

    def test_comprobar_mas_de_lo_autorizado_deja_por_comprobar_negativo(self):
        resultado = SaldoService.calcular_indicadores(saldo("5000.00", "1000.00", "1250.00"))

        self.assertEqual(resultado.por_comprobar, Decimal("-250.00"))
        self.assertEqual(resultado.porcentaje_gastado, Decimal("125.0"))


if __name__ == "__main__":
    unittest.main()
