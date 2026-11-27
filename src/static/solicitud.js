// Registro de solicitud de fondo (RF01/HU01, RF02/HU02) y seguimiento de su estado.
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, etiquetaEstado, dinero, CLASIFICACIONES } = window.Caja;
  const LIMITE_ADMINISTRACION = 5000;
  const $ = (id) => document.getElementById(id);
  // Quién solicita sale de la sesión iniciada (sesion.js); solo un residente ve esta pantalla
  const sesion = window.Sesion.actual();
  const residente = sesion && sesion.rol === window.Sesion.ROLES.RESIDENTE ? sesion.usuario : "";

  function mostrar() {
    $("registro").hidden = !residente;
    $("mis-solicitudes").hidden = !residente;
    $("residente-actual").textContent = residente ? "Solicitando como " + sesion.nombre + " (" + residente + ")" : "";
    if (residente) {
      cargarSolicitudes();
    }
  }

  // Obras existentes (su alta y su fondo viven en otro módulo); se elige, no se escribe.
  // El disponible se vuelve a consultar al elegir y tras cada envío para reflejar las aprobaciones.
  async function mostrarDisponible() {
    const nota = $("presupuesto-obra");
    const id = $("obra").value;
    nota.hidden = !id;
    if (!id) {
      return;
    }
    try {
      const obras = await llamar("/catalogo/obras");
      const obra = obras.find((o) => o.id === id);
      if (obra) {
        nota.textContent = "Caja chica disponible: " + dinero(obra.disponible_caja_chica)
          + " de " + dinero(obra.presupuesto_caja_chica);
      }
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function cargarObras() {
    try {
      const obras = await llamar("/catalogo/obras");
      $("obra").append(...obras.map((o) => el("option", { value: o.id, texto: o.nombre + " · " + o.id })));
      $("obra").addEventListener("change", mostrarDisponible);
      // La obra asignada al residente queda elegida; puede cambiarla si apoya otra obra
      if (sesion && sesion.obra_id && obras.some((o) => o.id === sesion.obra_id)) {
        $("obra").value = sesion.obra_id;
        mostrarDisponible();
      }
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function crearTarjeta(solicitud) {
    const decision = solicitud.autorizacion;
    const bloqueo = solicitud.bloqueo && solicitud.bloqueo.bloqueada ? solicitud.bloqueo : null;
    return el("li", {},
      el("div", { className: "tarjeta" + (bloqueo ? " bloqueada" : "") },
        el("h3", { texto: solicitud.folio }),
        etiquetaEstado(solicitud.estado),
        // RF04/HU04: el residente ve por qué su fondo no se autoriza todavía
        bloqueo ? el("p", { className: "alerta rojo", texto: bloqueo.mensaje }) : null,
        el("p", { texto: solicitud.concepto }),
        el("dl", {},
          el("dt", { texto: "Obra" }), el("dd", { texto: solicitud.obra_id }),
          el("dt", { texto: "Solicitado" }), el("dd", { texto: dinero(solicitud.monto_solicitado) }),
          decision && decision.monto_autorizado
            ? [el("dt", { texto: "Autorizado" }), el("dd", { texto: dinero(decision.monto_autorizado) })]
            : null,
          decision && decision.clasificacion
            ? [el("dt", { texto: "Se paga con" }), el("dd", { texto: CLASIFICACIONES[decision.clasificacion] })]
            : null,
          el("dt", { texto: "Autoriza" }), el("dd", { texto: solicitud.nivel_autorizacion })
        ),
        decision && decision.comentario ? el("p", { className: "nota", texto: decision.comentario }) : null,
        solicitud.estado === "Pendiente" ? crearCancelar(solicitud) : null
      )
    );
  }

  // Solo una solicitud que nadie ha decidido se puede retirar; es un borrado lógico (AGENTS.md §8)
  function crearCancelar(solicitud) {
    const boton = el("button", { type: "button", className: "secundario", texto: "Retirar solicitud" });
    boton.addEventListener("click", async () => {
      if (!confirm("¿Retirar " + solicitud.folio + "? Ya no aparecerá en la bandeja de autorización.")) {
        return;
      }
      try {
        await llamar("/solicitudes/" + solicitud.id, { method: "DELETE" });
        avisar(solicitud.folio + " retirada.");
        cargarSolicitudes();
      } catch (e) {
        avisar(e.message, true);
      }
    });
    return el("div", { className: "acciones inicio" }, boton);
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
      const bloqueo = respuesta.solicitud.bloqueo;
      if (bloqueo && bloqueo.bloqueada) {
        avisar(respuesta.solicitud.folio + " enviada, pero no se autorizará: " + bloqueo.mensaje, true);
      } else {
        avisar(respuesta.solicitud.folio + " enviada. " + respuesta.notificacion_enviada.mensaje);
      }
      $("form-solicitud").reset();
      $("vista-evidencia").hidden = true;
      $("campo-firma").hidden = true;
      $("presupuesto-obra").hidden = true;
      cargarSolicitudes();
    } catch (e) {
      avisar(e.message, true);
    }
  }

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

  cargarObras();
  mostrar();
})();
