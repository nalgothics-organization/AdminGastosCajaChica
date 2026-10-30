// Registro de solicitud de fondo (RF01/HU01, RF02/HU02) y seguimiento de su estado.
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, leer, guardar, etiquetaEstado, dinero, CLAVE_RESIDENTE } = window.Caja;
  const LIMITE_ADMINISTRACION = 5000;
  const $ = (id) => document.getElementById(id);
  let residente = leer(CLAVE_RESIDENTE);

  function mostrar() {
    $("config").hidden = Boolean(residente);
    $("registro").hidden = !residente;
    $("mis-solicitudes").hidden = !residente;
    $("residente-actual").textContent = residente ? "Solicitando como " + residente : "";
    if (residente) {
      cargarSolicitudes();
    }
  }

  function crearTarjeta(solicitud) {
    const decision = solicitud.autorizacion;
    return el("li", {},
      el("div", { className: "tarjeta" },
        el("h3", { texto: solicitud.folio }),
        etiquetaEstado(solicitud.estado),
        el("p", { texto: solicitud.concepto }),
        el("dl", {},
          el("dt", { texto: "Obra" }), el("dd", { texto: solicitud.obra_id }),
          el("dt", { texto: "Solicitado" }), el("dd", { texto: dinero(solicitud.monto_solicitado) }),
          decision && decision.monto_autorizado
            ? [el("dt", { texto: "Autorizado" }), el("dd", { texto: dinero(decision.monto_autorizado) })]
            : null,
          el("dt", { texto: "Autoriza" }), el("dd", { texto: solicitud.nivel_autorizacion })
        ),
        decision && decision.comentario ? el("p", { className: "nota", texto: decision.comentario }) : null
      )
    );
  }

  async function cargarSolicitudes() {
    try {
      const todas = await llamar("/solicitudes");
      const mias = todas.filter((s) => s.solicitante_id === residente).reverse();
      $("lista-solicitudes").replaceChildren(...mias.map(crearTarjeta));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function leerFormulario() {
    const form = $("form-solicitud");
    const datos = {
      solicitante_id: residente,
      obra_id: form.elements.obra_id.value,
      etapa_construccion: form.elements.etapa_construccion.value,
      partida_categoria: form.elements.partida_categoria.value,
      concepto: form.elements.concepto.value,
      monto_solicitado: form.elements.monto_solicitado.value || null,
      costo_estimado: form.elements.costo_estimado.value || null,
      urgencia: form.elements.urgencia.value,
      evidencia_url: form.elements.evidencia_url.value,
    };
    if (Number(datos.monto_solicitado) > LIMITE_ADMINISTRACION) {
      datos.firma_digital_direccion = form.elements.firma_digital_direccion.value || null;
    }
    return datos;
  }

  async function enviar(evento) {
    evento.preventDefault();
    try {
      const respuesta = await llamar("/solicitudes", enviarJson("POST", leerFormulario()));
      avisar(respuesta.solicitud.folio + " enviada. " + respuesta.notificacion_enviada.mensaje);
      $("form-solicitud").reset();
      $("vista-evidencia").hidden = true;
      $("campo-firma").hidden = true;
      cargarSolicitudes();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("guardar-residente").addEventListener("click", () => {
    const valor = $("residente").value.trim();
    if (valor) {
      residente = valor;
      guardar(CLAVE_RESIDENTE, valor);
      mostrar();
    }
  });
  $("monto").addEventListener("input", () => {
    $("campo-firma").hidden = Number($("monto").value) <= LIMITE_ADMINISTRACION;
  });
  $("form-solicitud").addEventListener("submit", enviar);

  // La foto se sube al elegirla y su URL queda como evidencia de la solicitud
  async function subirEvidencia(evento) {
    const archivo = evento.target.files[0];
    evento.target.value = "";
    if (!archivo) {
      return;
    }
    const datos = new FormData();
    datos.append("imagen", archivo);
    try {
      const respuesta = await llamar("/solicitudes/evidencia", { method: "POST", body: datos });
      $("evidencia").value = respuesta.evidencia_url;
      $("vista-evidencia").src = URL.createObjectURL(archivo);
      $("vista-evidencia").hidden = false;
      avisar("Fotografía adjuntada como evidencia.");
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("foto-evidencia").addEventListener("change", subirEvidencia);
  $("archivo-evidencia").addEventListener("change", subirEvidencia);

  mostrar();
})();
