// Interfaz de captura en obra (RNF01/HU16) y formulario de comprobación (RF07/HU07).
(function () {
  "use strict";

  const API = "/api";
  const CLAVE_RESIDENTE = "cajaChica.residente";
  // Espejo de PARTIDAS_CON_HORAS (src/models/comprobante.py); el backend valida de todos modos
  const PARTIDAS_CON_HORAS = ["renta de maquinaria", "mano de obra"];

  const $ = (id) => document.getElementById(id);
  let residente = leerResidente();
  let comprobanteActual = null;
  let solicitudesAprobadas = [];

  function leerResidente() {
    try {
      return localStorage.getItem(CLAVE_RESIDENTE) || "";
    } catch (e) {
      return "";
    }
  }

  function guardarResidente(valor) {
    residente = valor;
    try {
      localStorage.setItem(CLAVE_RESIDENTE, valor);
    } catch (e) {
      // Sin almacenamiento local el residente se pide de nuevo en la siguiente visita
    }
  }

  function avisar(mensaje, esError) {
    const aviso = $("aviso");
    aviso.textContent = mensaje;
    aviso.classList.toggle("error", Boolean(esError));
    aviso.hidden = false;
    clearTimeout(avisar.temporizador);
    avisar.temporizador = setTimeout(() => { aviso.hidden = true; }, 4000);
  }

  async function llamar(ruta, opciones) {
    const respuesta = await fetch(API + ruta, opciones);
    if (respuesta.status === 204) {
      return null;
    }
    const cuerpo = await respuesta.json();
    if (!respuesta.ok) {
      const detalle = Array.isArray(cuerpo.detail)
        ? cuerpo.detail.map((d) => d.msg).join(" ")
        : cuerpo.detail;
      throw new Error(detalle || "Error al comunicarse con el servidor.");
    }
    return cuerpo;
  }

  function mostrarPantalla() {
    $("config").hidden = Boolean(residente);
    $("captura").hidden = !residente;
    $("pendientes").hidden = !residente;
    $("formulario").hidden = true;
    $("residente-actual").textContent = residente ? "Capturando como " + residente : "";
    if (residente) {
      cargarPendientes();
    }
  }

  async function subirFoto(archivo) {
    const datos = new FormData();
    datos.append("solicitante_id", residente);
    datos.append("imagen", archivo);
    try {
      const comprobante = await llamar("/comprobantes/captura", { method: "POST", body: datos });
      avisar(comprobante.solicitud_id
        ? "Comprobante guardado. Complete los datos cuando pueda."
        : "Foto guardada. Elija la solicitud al completar los datos.");
      cargarPendientes();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function cargarPendientes() {
    const lista = $("lista-pendientes");
    try {
      const borradores = await llamar(
        "/comprobantes?estado=Borrador&solicitante_id=" + encodeURIComponent(residente)
      );
      lista.replaceChildren(...borradores.map(crearElementoPendiente));
      $("pendientes").hidden = borradores.length === 0;
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function crearElementoPendiente(comprobante) {
    const boton = document.createElement("button");
    boton.type = "button";
    boton.className = "secundario";
    const fecha = new Date(comprobante.created_at).toLocaleString("es-MX");
    boton.textContent = (comprobante.datos ? "Listo para cerrar · " : "Sin datos · ") + fecha;
    boton.addEventListener("click", () => abrirFormulario(comprobante));
    const item = document.createElement("li");
    item.appendChild(boton);
    return item;
  }

  async function abrirFormulario(comprobante) {
    comprobanteActual = comprobante;
    const form = $("form-datos");
    form.reset();
    const datos = comprobante.datos || {};
    form.elements.fecha_gasto.value = datos.fecha_gasto || new Date().toISOString().slice(0, 10);
    form.elements.monto_comprobado.value = datos.monto_comprobado || "";
    form.elements.proveedor.value = datos.proveedor || "";
    form.elements.concepto.value = datos.concepto || "";
    form.elements.horas.value = datos.horas || "";
    if (datos.unidad_horas) {
      form.elements.unidad_horas.value = datos.unidad_horas;
    }
    if (datos.obra_id) {
      form.elements.obra_id.value = datos.obra_id;
      form.elements.etapa_construccion.value = datos.etapa_construccion;
      form.elements.partida_categoria.value = datos.partida_categoria;
    }
    if (datos.tipo) {
      form.querySelector('input[name="tipo"][value="' + datos.tipo + '"]').checked = true;
    }

    $("campo-solicitud").hidden = Boolean(comprobante.solicitud_id);
    if (!comprobante.solicitud_id) {
      await cargarSolicitudes();
    }
    actualizarCampoHoras();

    $("captura").hidden = true;
    $("pendientes").hidden = true;
    $("formulario").hidden = false;
  }

  async function cargarSolicitudes() {
    const select = $("solicitud");
    try {
      const solicitudes = await llamar("/solicitudes");
      solicitudesAprobadas = solicitudes.filter(
        (s) => s.solicitante_id === residente && s.estado === "Aprobado"
      );
    } catch (e) {
      solicitudesAprobadas = [];
      avisar(e.message, true);
    }
    const opciones = solicitudesAprobadas.map((s) => {
      const opcion = document.createElement("option");
      opcion.value = s.id;
      opcion.textContent = s.folio + " · " + s.concepto;
      return opcion;
    });
    // El residente también puede comprobar un gasto que pagó antes de pedir fondos
    const sinSolicitud = document.createElement("option");
    sinSolicitud.value = "";
    sinSolicitud.textContent = "Lo pagué por mi cuenta (sin solicitud)";
    select.replaceChildren(...opciones, sinSolicitud);
  }

  function pagoSinSolicitud() {
    return !comprobanteActual.solicitud_id && $("solicitud").value === "";
  }

  // Muestra las horas solo cuando la partida de la solicitud las exige (RF07)
  function actualizarCampoHoras() {
    const sinSolicitud = pagoSinSolicitud();
    $("campo-clasificacion").hidden = !sinSolicitud;
    let requiere = comprobanteActual && comprobanteActual.requiere_horas;
    if (sinSolicitud) {
      requiere = PARTIDAS_CON_HORAS.includes($("partida-gasto").value.trim().toLowerCase());
    } else if (requiere === null || requiere === undefined) {
      const elegida = solicitudesAprobadas.find((s) => s.id === $("solicitud").value);
      requiere = Boolean(elegida)
        && PARTIDAS_CON_HORAS.includes(elegida.partida_categoria.trim().toLowerCase());
    }
    $("campo-horas").hidden = !requiere;
    $("horas").required = requiere;
  }

  function leerFormulario() {
    const form = $("form-datos");
    const tipo = form.querySelector('input[name="tipo"]:checked');
    const conHoras = !$("campo-horas").hidden;
    const sinSolicitud = pagoSinSolicitud();
    return {
      obra_id: sinSolicitud ? form.elements.obra_id.value : null,
      etapa_construccion: sinSolicitud ? form.elements.etapa_construccion.value : null,
      partida_categoria: sinSolicitud ? form.elements.partida_categoria.value : null,
      tipo: tipo ? tipo.value : null,
      monto_comprobado: form.elements.monto_comprobado.value || null,
      fecha_gasto: form.elements.fecha_gasto.value || null,
      proveedor: form.elements.proveedor.value,
      concepto: form.elements.concepto.value,
      horas: conHoras ? form.elements.horas.value || null : null,
      unidad_horas: conHoras ? form.elements.unidad_horas.value : null,
      solicitud_id: comprobanteActual.solicitud_id ? null : form.elements.solicitud_id.value || null,
    };
  }

  async function enviarFormulario(evento) {
    evento.preventDefault();
    const accion = evento.submitter ? evento.submitter.dataset.accion : "guardar";
    const id = comprobanteActual.id;
    try {
      comprobanteActual = await llamar("/comprobantes/" + id + "/datos", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(leerFormulario()),
      });
      if (accion === "cerrar") {
        const cerrado = await llamar("/comprobantes/" + id + "/cerrar", { method: "POST" });
        avisar("Comprobación cerrada: " + cerrado.estado + ".");
      } else {
        avisar("Datos guardados.");
      }
      mostrarPantalla();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function descartar() {
    try {
      await llamar("/comprobantes/" + comprobanteActual.id, { method: "DELETE" });
      avisar("Borrador descartado.");
      mostrarPantalla();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("guardar-residente").addEventListener("click", () => {
    const valor = $("residente").value.trim();
    if (valor) {
      guardarResidente(valor);
      mostrarPantalla();
    }
  });

  $("foto").addEventListener("change", (evento) => {
    const archivo = evento.target.files[0];
    // Se limpia para que la misma foto pueda volver a seleccionarse si falla la subida
    evento.target.value = "";
    if (archivo) {
      subirFoto(archivo);
    }
  });

  $("solicitud").addEventListener("change", actualizarCampoHoras);
  $("partida-gasto").addEventListener("change", actualizarCampoHoras);
  $("form-datos").addEventListener("submit", enviarFormulario);
  $("descartar").addEventListener("click", descartar);
  $("volver").addEventListener("click", mostrarPantalla);

  mostrarPantalla();
})();
