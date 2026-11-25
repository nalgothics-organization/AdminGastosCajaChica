"""Revisión de legibilidad del comprobante con OCR (RNF05/HU21).

Una foto solo se guarda si el texto se lee y parece un ticket o una factura: un plano, un teclado o una
foto borrosa u oscura se rechazan con un mensaje para repetirla. Usa RapidOCR (modelos ONNX incluidos en
el paquete, sin descargas ni programas externos).
Reglas de codificación: UTF-8, LF, 4 espacios de indentación.
"""

import re
import threading
from io import BytesIO
from typing import List, Optional, Tuple

import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

# Lado mayor al que se reduce la foto antes de leerla: suficiente para un ticket y ~2 s por foto
LADO_MAXIMO_OCR = 1600
# Un ticket legible da decenas de renglones; con menos, la foto no se lee (borrosa, oscura o sin texto)
MINIMO_CAJAS_DE_TEXTO = 5
# Confianza media del OCR: los tickets nítidos dan 0.94 o más y los borrosos caen o no se leen
CONFIANZA_MINIMA = 0.85
# Un comprobante trae al menos un monto: "$125", "$1,250.50" o "125.00"
MONTO = re.compile(r"\$\s*\d|\d{1,3}(?:[.,]\d{3})*[.,]\d{2}\b")

MENSAJE_SIN_TEXTO = (
    "No se alcanza a leer texto en la foto: salió borrosa, oscura o no es un comprobante. "
    "Repítela bien enfocada y con buena luz."
)
MENSAJE_BORROSA = "La foto salió borrosa y el texto no se lee bien. Repítela bien enfocada."
MENSAJE_SIN_MONTO = (
    "No parece un ticket o una factura: no se encontró ningún monto. Fotografía el comprobante completo."
)
MENSAJE_NO_ES_IMAGEN = "El archivo no es una imagen válida."

_motor = None
# El motor ONNX se comparte entre peticiones; se serializa su uso para no depender de su hilo seguro
_candado = threading.Lock()


def _preparar_imagen(contenido: bytes) -> np.ndarray:
    """Decodifica la foto, corrige su orientación y la reduce; devuelve píxeles BGR para el OCR."""
    try:
        imagen = ImageOps.exif_transpose(Image.open(BytesIO(contenido))).convert("RGB")
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError):
        raise ValueError(MENSAJE_NO_ES_IMAGEN) from None
    imagen.thumbnail((LADO_MAXIMO_OCR, LADO_MAXIMO_OCR))
    return np.ascontiguousarray(np.asarray(imagen)[:, :, ::-1])


def leer_texto(contenido: bytes) -> Tuple[List[str], List[float]]:
    """Devuelve los renglones de texto que se leen en la foto y la confianza de cada uno."""
    global _motor
    pixeles = _preparar_imagen(contenido)
    with _candado:
        if _motor is None:
            from rapidocr import RapidOCR  # se importa aquí para no cargar el OCR si no se usa

            _motor = RapidOCR()
        resultado = _motor(pixeles)
    textos = list(resultado.txts) if resultado.txts is not None else []
    confianzas = [float(c) for c in resultado.scores] if resultado.scores is not None else []
    return textos, confianzas


def motivo_de_rechazo(textos: List[str], confianzas: List[float]) -> Optional[str]:
    """Explica por qué la lectura no es de un comprobante; None si la foto es aceptable."""
    if len(textos) < MINIMO_CAJAS_DE_TEXTO:
        return MENSAJE_SIN_TEXTO
    if sum(confianzas) / len(confianzas) < CONFIANZA_MINIMA:
        return MENSAJE_BORROSA
    if not any(MONTO.search(texto) for texto in textos):
        return MENSAJE_SIN_MONTO
    return None


def revisar_legibilidad(contenido: bytes) -> Tuple[List[str], List[float]]:
    """Devuelve el texto leído de la foto; lanza ValueError con el motivo si no es un comprobante legible."""
    textos, confianzas = leer_texto(contenido)
    motivo = motivo_de_rechazo(textos, confianzas)
    if motivo:
        raise ValueError(motivo)
    return textos, confianzas
