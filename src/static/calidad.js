// Revisión de la foto en el dispositivo (RNF05/HU21): detecta fotos oscuras o borrosas.
// Se separa de app.js para poder probarla con Node (tests/test_escaneo_calidad.py).
(function (raiz) {
  "use strict";

  // Umbrales: luminancia media 0-255 y varianza del laplaciano
  const UMBRAL_OSCURA = 45;
  const UMBRAL_BORROSA = 100;

  // Recibe los píxeles RGBA de la imagen reducida; oscura = poca luz, borrosa = pocos bordes definidos
  function evaluarCalidad(pixeles, ancho, alto) {
    const gris = new Float32Array(ancho * alto);
    let suma = 0;
    for (let i = 0; i < gris.length; i++) {
      gris[i] = 0.299 * pixeles[i * 4] + 0.587 * pixeles[i * 4 + 1] + 0.114 * pixeles[i * 4 + 2];
      suma += gris[i];
    }
    const luminancia = suma / gris.length;
    let acumulado = 0;
    let acumuladoCuadrado = 0;
    let cuenta = 0;
    for (let y = 1; y < alto - 1; y++) {
      for (let x = 1; x < ancho - 1; x++) {
        const i = y * ancho + x;
        const laplaciano = 4 * gris[i] - gris[i - 1] - gris[i + 1] - gris[i - ancho] - gris[i + ancho];
        acumulado += laplaciano;
        acumuladoCuadrado += laplaciano * laplaciano;
        cuenta++;
      }
    }
    const media = acumulado / cuenta;
    const nitidez = acumuladoCuadrado / cuenta - media * media;
    return { oscura: luminancia < UMBRAL_OSCURA, borrosa: nitidez < UMBRAL_BORROSA };
  }

  const CalidadFoto = { evaluarCalidad, UMBRAL_OSCURA, UMBRAL_BORROSA };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = CalidadFoto;
  } else {
    raiz.CalidadFoto = CalidadFoto;
  }
})(this);
