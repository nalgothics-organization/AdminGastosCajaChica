// Aviso inmediato en el dispositivo cuando la foto salió a oscuras (RNF05/HU21).
// La nitidez y el contenido (que sea un ticket) los revisa el servidor con OCR; aquí solo se mide la luz.
// Se separa de app.js para poder probarla con Node (tests/test_escaneo_calidad.py).
(function (raiz) {
  "use strict";

  // Luminancia media 0-255 por debajo de la cual la foto se considera oscura
  const UMBRAL_OSCURA = 45;

  // Recibe los píxeles RGBA de la imagen reducida
  function evaluarCalidad(pixeles, ancho, alto) {
    let suma = 0;
    const total = ancho * alto;
    for (let i = 0; i < total; i++) {
      suma += 0.299 * pixeles[i * 4] + 0.587 * pixeles[i * 4 + 1] + 0.114 * pixeles[i * 4 + 2];
    }
    return { oscura: suma / total < UMBRAL_OSCURA };
  }

  const CalidadFoto = { evaluarCalidad, UMBRAL_OSCURA };
  if (typeof module !== "undefined" && module.exports) {
    module.exports = CalidadFoto;
  } else {
    raiz.CalidadFoto = CalidadFoto;
  }
})(this);
