"""Extracción de datos del comprobante a partir del texto que lee el OCR (RF11/HU11).

Busca el monto, la fecha, el proveedor y el tipo en los renglones leídos de la foto. Lo que no se
reconoce queda en None para que el residente lo complete; nunca se inventa un valor.
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import re
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from src.models.comprobante import LecturaComprobante, TipoComprobante

# Un monto: "$125", "$1,250.50" o un número con dos decimales ("125.00", "1.250,50")
MONTO = re.compile(r"\$\s*\d[\d.,]*|(?<![\d.,])\d{1,3}(?:[.,]\d{3})*[.,]\d{2}(?![\d])|(?<![\d.,])\d+[.,]\d{2}(?![\d])")

MESES = {
    "ene": 1, "jan": 1, "feb": 2, "mar": 3, "abr": 4, "apr": 4, "may": 5, "jun": 6, "jul": 7,
    "ago": 8, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dic": 12, "dec": 12,
}
FECHA_NUMERICA = re.compile(r"(?<!\d)(\d{1,2})\s*[/.-]\s*(\d{1,2})\s*[/.-]\s*(\d{4}|\d{2})(?!\d)")
FECHA_ISO = re.compile(r"(?<!\d)(\d{4})\s*[/-]\s*(\d{1,2})\s*[/-]\s*(\d{1,2})(?!\d)")
FECHA_MES_PRIMERO = re.compile(r"\b([a-záéíóú]{3,10})\.?\s+(\d{1,2})\s*,?\s*(\d{4})\b", re.IGNORECASE)
FECHA_DIA_PRIMERO = re.compile(r"\b(\d{1,2})\s*(?:de\s+)?[-/ ]?\s*([a-záéíóú]{3,10})\.?\s*(?:de\s+)?[-/ ]?\s*(\d{4})\b", re.IGNORECASE)

# Renglones que no son el nombre del comercio
NO_ES_PROVEEDOR = (
    "fecha", "hora", "ticket", "factura", "folio", "rfc", "total", "subtotal", "iva", "cambio", "gracias",
    "bienvenid", "transacci", "venta", "autoriza", "tarjeta", "recibo", "cliente", "caja", "sucursal",
    "tel", "www", "http", "cfdi", "uuid", "no.", "num",
)
PALABRAS_FACTURA = ("factura", "cfdi", "folio fiscal", "comprobante fiscal", "uuid")
PALABRAS_TICKET = ("ticket", "total", "subtotal", "cambio", "voucher", "venta", "transacci", "recibo", "iva")
MAXIMO_RENGLONES = 60
LARGO_PROVEEDOR = 120


def _a_decimal(texto: str) -> Optional[Decimal]:
    """Convierte "$1,250.50", "1.250,50" o "125,00" en Decimal; None si no es un monto."""
    limpio = texto.replace("$", "").replace(" ", "")
    if not limpio or not limpio[0].isdigit():
        return None
    ultimo = max(limpio.rfind("."), limpio.rfind(","))
    if ultimo == -1:
        entero, decimales = limpio, ""
    else:
        entero, decimales = limpio[:ultimo], limpio[ultimo + 1:]
        if len(decimales) == 3 and "." in entero + decimales and "," in entero + decimales:
            # "1,250.500" no es un monto válido
            return None
        if len(decimales) not in (0, 1, 2):
            # Un solo separador con tres dígitos detrás es de miles: "1,250" o "1.250"
            entero, decimales = limpio, ""
    entero = re.sub(r"[.,]", "", entero)
    try:
        return Decimal(f"{entero}.{decimales}" if decimales else entero).quantize(Decimal("0.01"))
    except InvalidOperation:
        return None


def _montos_de(renglon: str) -> List[Decimal]:
    montos = [_a_decimal(coincidencia.group()) for coincidencia in MONTO.finditer(renglon)]
    return [monto for monto in montos if monto is not None and monto > 0]


def extraer_monto(renglones: List[str]) -> Optional[Decimal]:
    """El monto del renglón "Total" (o el siguiente); si no hay, el mayor de los montos leídos."""
    de_total: List[Decimal] = []
    for posicion, renglon in enumerate(renglones):
        minuscula = renglon.lower()
        if "total" not in minuscula or "subtotal" in minuscula:
            continue
        montos = _montos_de(renglon) or (_montos_de(renglones[posicion + 1]) if posicion + 1 < len(renglones) else [])
        de_total.extend(montos)
    if de_total:
        return max(de_total)
    todos = [monto for renglon in renglones for monto in _montos_de(renglon)]
    return max(todos) if todos else None


def _fecha_valida(dia: int, mes: int, anio: int) -> Optional[date]:
    if anio < 100:
        anio += 2000
    try:
        fecha = date(anio, mes, dia)
    except ValueError:
        return None
    # Un gasto no puede ser del futuro ni de hace décadas (un número de folio suele parecer fecha)
    return fecha if date(2000, 1, 1) <= fecha <= date.today() else None


def _mes(nombre: str) -> Optional[int]:
    return MESES.get(nombre.lower()[:3])


def extraer_fecha(renglones: List[str]) -> Optional[date]:
    """La primera fecha válida, de arriba hacia abajo, en formatos como 13/11/2026 o Nov. 13, 2026."""
    for renglon in renglones:
        candidatas = []
        for dia, mes, anio in (m.groups() for m in FECHA_NUMERICA.finditer(renglon)):
            # En México se escribe día/mes/año; si el "mes" no puede serlo, se lee mes/día/año
            primero, segundo = int(dia), int(mes)
            candidatas.append((primero, segundo, int(anio)) if segundo <= 12 else (segundo, primero, int(anio)))
        candidatas += [(int(d), int(m), int(a)) for a, m, d in (m.groups() for m in FECHA_ISO.finditer(renglon))]
        for nombre, dia, anio in (m.groups() for m in FECHA_MES_PRIMERO.finditer(renglon)):
            if _mes(nombre):
                candidatas.append((int(dia), _mes(nombre), int(anio)))
        for dia, nombre, anio in (m.groups() for m in FECHA_DIA_PRIMERO.finditer(renglon)):
            if _mes(nombre):
                candidatas.append((int(dia), _mes(nombre), int(anio)))
        for dia, mes, anio in candidatas:
            fecha = _fecha_valida(dia, mes, anio)
            if fecha:
                return fecha
    return None


def extraer_proveedor(renglones: List[str]) -> Optional[str]:
    """El primer renglón de arriba que parece el nombre de un comercio (letras, sin datos del cobro)."""
    for renglon in renglones[:6]:
        texto = renglon.strip()
        letras = sum(caracter.isalpha() for caracter in texto)
        if letras < 3 or letras / len(texto) < 0.6:
            continue
        if any(palabra in texto.lower() for palabra in NO_ES_PROVEEDOR) or _montos_de(texto):
            continue
        return texto[:LARGO_PROVEEDOR]
    return None


def extraer_tipo(renglones: List[str]) -> Optional[TipoComprobante]:
    """Factura si se menciona; ticket si tiene datos de una venta. Una nota a mano no se reconoce."""
    texto = " ".join(renglones).lower()
    if any(palabra in texto for palabra in PALABRAS_FACTURA):
        return TipoComprobante.FACTURA
    if any(palabra in texto for palabra in PALABRAS_TICKET):
        return TipoComprobante.TICKET
    return None


def extraer_datos(renglones: List[str], confianzas: List[float]) -> LecturaComprobante:
    """Reúne lo que se reconoce de la foto; lo demás queda en None (por completar)."""
    limpios = [renglon.strip() for renglon in renglones if renglon and renglon.strip()]
    return LecturaComprobante(
        tipo=extraer_tipo(limpios),
        monto_comprobado=extraer_monto(limpios),
        fecha_gasto=extraer_fecha(limpios),
        proveedor=extraer_proveedor(limpios),
        renglones=limpios[:MAXIMO_RENGLONES],
        confianza=round(sum(confianzas) / len(confianzas), 3) if confianzas else None,
    )
