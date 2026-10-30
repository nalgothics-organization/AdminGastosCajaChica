// Mi caja chica: se elige una solicitud aprobada, se ve su resumen y se sube el comprobante
// (RNF01/HU16); los datos se completan después en el formulario de comprobación (RF07/HU07).
(function () {
  "use strict";

  const API = "/api";
  const CLAVE_RESIDENTE = "cajaChica.residente";
  // Espejo de PARTIDAS_CON_HORAS (src/models/comprobante.py); el backend valida de todos modos
  const PARTIDAS_CON_HORAS = ["renta de maquinaria", "mano de obra"];
  const PROPIA = "propia"; // gasto que el residente pagó por su cuenta, sin solicitud previa
  const ESTADOS_CERRADOS = ["Comprobado", "Revisión contabilidad"];

  const $ = (id) => document.getElementById(id);
  const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
  const dinero = (valor) => moneda.format(Number(valor));
  let residente = leerResidente();
  let comprobanteActual = null;
  let seleccion = null; // id de la solicitud elegida o PROPIA
  let solicitudes = [];
  let comprobantes = [];
  let saldos = [];

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

  // Crea un elemento con texto seguro (nunca interpreta HTML de los datos)
  function el(etiqueta, clase, texto, ...hijos) {
    const nodo = document.createElement(etiqueta);
    if (clase) {
      nodo.className = clase;
    }
    if (texto !== null && texto !== undefined) {
      nodo.textContent = texto;
    }
    hijos.forEach((hijo) => hijo && nodo.append(hijo));
    return nodo;
  }

  const pastilla = (texto, color) => el("span", "pastilla " + color, texto);

  function montoAutorizado(solicitud) {
    const decision = solicitud.autorizacion;
    return decision && decision.monto_autorizado ? decision.monto_autorizado : solicitud.monto_solicitado;
  }

  function solicitudElegida() {
    return solicitudes.find((s) => s.id === seleccion) || null;
  }

  function comprobantesDe(idSolicitud) {
    return comprobantes.filter((c) => (c.solicitud_id || null) === idSolicitud);
  }

  // Un ajuste sustituye al original y un reverso lo anula; el reverso mismo no suma gasto
  function comprobadoDe(idSolicitud) {
    const cerrados = comprobantesDe(idSolicitud).filter((c) => ESTADOS_CERRADOS.includes(c.estado) && c.datos);
    const corregidos = new Set(
      cerrados.filter((c) => c.tipo_registro !== "original").map((c) => c.comprobante_origen_id)
    );
    return cerrados
      .filter((c) => c.tipo_registro === "ajuste" || (c.tipo_registro === "original" && !corregidos.has(c.id)))
      .reduce((total, c) => total + Number(c.datos.monto_comprobado), 0);
  }

  async function cargarDatos() {
    const [todas, propios, resumenObras] = await Promise.all([
      llamar("/solicitudes"),
      llamar("/comprobantes?solicitante_id=" + encodeURIComponent(residente)),
      llamar("/saldos"),
    ]);
    solicitudes = todas.filter((s) => s.solicitante_id === residente && s.estado === "Aprobado");
    comprobantes = propios;
    saldos = resumenObras;
    // Con una sola solicitud aprobada se elige sola para llegar a la cámara en 3 toques (RNF01)
    if (!seleccion && solicitudes.length === 1) {
      seleccion = solicitudes[0].id;
    }
    if (seleccion && seleccion !== PROPIA && !solicitudElegida()) {
      seleccion = null;
    }
  }

  async function mostrarPantalla() {
    $("config").hidden = Boolean(residente);
    $("mi-caja").hidden = !residente;
    $("formulario").hidden = true;
    $("residente-actual").textContent = residente ? "Capturando como " + residente : "";
    if (!residente) {
      return;
    }
    try {
      await cargarDatos();
      renderizar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function renderizar() {
    $("sin-solicitudes").hidden = solicitudes.length > 0;
    $("lista-solicitudes").replaceChildren(
      ...solicitudes.map(crearOpcionSolicitud),
      crearOpcionPropia()
    );
    renderizarResumen();
  }

  function crearOpcion(clase, ...hijos) {
    const boton = el("button", "opcion " + clase, null, ...hijos);
    boton.type = "button";
    return boton;
  }

  function crearOpcionSolicitud(solicitud) {
    const boton = crearOpcion(
      solicitud.id === seleccion ? "elegida" : "",
      el("strong", "mono", solicitud.folio),
      el("span", "", solicitud.concepto),
      el("small", "", solicitud.obra_id + " · " + dinero(montoAutorizado(solicitud))),
      comprobadoDe(solicitud.id) > 0 ? pastilla("Con comprobantes", "verde") : pastilla("Por comprobar", "ambar")
    );
    boton.addEventListener("click", () => elegir(solicitud.id));
    return el("li", "", null, boton);
  }

  function crearOpcionPropia() {
    const boton = crearOpcion(
      (seleccion === PROPIA ? "elegida " : "") + "propia",
      el("strong", "", "Gasto pagado por mi cuenta"),
      el("small", "", "Sin solicitud previa: se reembolsa después de revisarlo")
    );
    boton.addEventListener("click", () => elegir(PROPIA));
    return el("li", "", null, boton);
  }

  function elegir(id) {
    seleccion = id;
    renderizar();
  }

  function renderizarResumen() {
    const solicitud = solicitudElegida();
    $("resumen").hidden = !seleccion;
    if (!seleccion) {
      return;
    }
    $("resumen-titulo").textContent = solicitud ? "Resumen de " + solicitud.folio : "Gasto pagado por mi cuenta";
    $("resumen-detalle").replaceChildren(...(solicitud
      ? [crearResumenSolicitud(solicitud), crearPanelObra(solicitud.obra_id)]
      : [el("p", "nota", "No pertenece a ninguna solicitud: al completar los datos indicarás la obra, la etapa y la partida.")]));

    const lista = comprobantesDe(solicitud ? solicitud.id : null);
    $("sin-comprobantes").hidden = lista.length > 0;
    $("lista-comprobantes").replaceChildren(...lista.slice().reverse().map(crearElementoComprobante));
  }

  function crearResumenSolicitud(solicitud) {
    const autorizado = Number(montoAutorizado(solicitud));
    const comprobado = comprobadoDe(solicitud.id);
    return el("div", "tarjeta", null,
      el("h3", "", solicitud.folio),
      el("p", "", solicitud.concepto),
      el("dl", "", null,
        el("dt", "", "Obra"), el("dd", "", solicitud.obra_id),
        el("dt", "", "Etapa"), el("dd", "", solicitud.etapa_construccion),
        el("dt", "", "Partida"), el("dd", "", solicitud.partida_categoria),
        el("dt", "", "Autorizado"), el("dd", "", dinero(autorizado)),
        el("dt", "", "Comprobado"), el("dd", "", dinero(comprobado)),
        el("dt", "", "Por comprobar"),
        el("dd", autorizado - comprobado < 0 ? "negativo" : "", dinero(autorizado - comprobado))));
  }

  // Caja chica solo de la obra de la solicitud elegida, no la de todas las obras
  function crearPanelObra(obraId) {
    const saldo = saldos.find((s) => s.obra_id === obraId);
    if (!saldo) {
      return el("div", "tarjeta", null, el("p", "nota", "Sin información de caja chica para esta obra."));
    }
    const porcentaje = Number(saldo.porcentaje_autorizado);
    const claseBarra = porcentaje > 100 ? "excedido" : porcentaje >= 80 ? "alerta" : "";
    const relleno = el("span");
    relleno.style.width = Math.min(porcentaje, 100) + "%";
    return el("div", "tarjeta", null,
      el("h3", "", "Caja chica · " + saldo.nombre),
      el("p", "cifra" + (Number(saldo.disponible_caja_chica) < 0 ? " negativo" : ""), dinero(saldo.disponible_caja_chica)),
      el("p", "nota", "disponible de " + dinero(saldo.presupuesto_caja_chica)),
      el("div", "barra " + claseBarra, null, relleno),
      el("p", "nota", porcentaje + "% del fondo ya está autorizado"),
      el("dl", "", null,
        el("dt", "", "Autorizado en la obra"), el("dd", "", dinero(saldo.autorizado)),
        el("dt", "", "Comprobado en la obra"), el("dd", "", dinero(saldo.comprobado)),
        el("dt", "", "Por comprobar en la obra"), el("dd", "", dinero(saldo.por_comprobar))));
  }

  function crearElementoComprobante(comprobante) {
    const fecha = new Date(comprobante.created_at).toLocaleString("es-MX");
    if (comprobante.estado === "Borrador") {
      const boton = el("button", "secundario", (comprobante.datos ? "Listo para cerrar · " : "Completar datos · ") + fecha);
      boton.type = "button";
      boton.addEventListener("click", () => abrirFormulario(comprobante));
      return el("li", "", null, boton);
    }
    const monto = comprobante.datos ? dinero(comprobante.datos.monto_comprobado) : "";
    const color = comprobante.estado === "Comprobado" ? "verde" : "morado";
    return el("li", "fila-comprobante", null,
      el("span", "", fecha + " · " + monto), pastilla(comprobante.estado, color));
  }

  async function subirFoto(archivo) {
    const datos = new FormData();
    datos.append("solicitante_id", residente);
    if (seleccion && seleccion !== PROPIA) {
      datos.append("solicitud_id", seleccion);
    }
    datos.append("imagen", archivo);
    try {
      await llamar("/comprobantes/captura", { method: "POST", body: datos });
      avisar("Foto guardada. Completa los datos desde la lista para enviarla a revisión.");
      mostrarPantalla();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function abrirFormulario(comprobante) {
    await obrasListas;
    comprobanteActual = comprobante;
    const solicitud = solicitudes.find((s) => s.id === comprobante.solicitud_id);
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
    if (comprobante.obra_id && !comprobante.solicitud_id) {
      form.elements.obra_id.value = comprobante.obra_id;
      form.elements.etapa_construccion.value = comprobante.etapa_construccion;
      form.elements.partida_categoria.value = comprobante.partida_categoria;
    }
    if (datos.tipo) {
      form.querySelector('input[name="tipo"][value="' + datos.tipo + '"]').checked = true;
    }

    $("formulario-solicitud").textContent = solicitud
      ? "Solicitud " + solicitud.folio + " · " + solicitud.obra_id
      : "Gasto pagado por mi cuenta";
    actualizarCampoHoras();

    $("mi-caja").hidden = true;
    $("formulario").hidden = false;
  }

  function pagoSinSolicitud() {
    return !comprobanteActual.solicitud_id;
  }

  // Muestra las horas solo cuando la partida exige maquinaria o trabajo (RF07)
  function actualizarCampoHoras() {
    const sinSolicitud = pagoSinSolicitud();
    $("campo-clasificacion").hidden = !sinSolicitud;
    const partida = sinSolicitud ? $("partida-gasto").value : comprobanteActual.partida_categoria || "";
    const requiere = PARTIDAS_CON_HORAS.includes(partida.trim().toLowerCase());
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
      solicitud_id: comprobanteActual.solicitud_id || null,
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
        avisar("Comprobación enviada: " + cerrado.estado + ".");
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

  function alElegirArchivo(evento) {
    const archivo = evento.target.files[0];
    // Se limpia para que la misma foto pueda volver a seleccionarse si falla la subida
    evento.target.value = "";
    if (archivo) {
      subirFoto(archivo);
    }
  }

  $("guardar-residente").addEventListener("click", () => {
    const valor = $("residente").value.trim();
    if (valor) {
      guardarResidente(valor);
      mostrarPantalla();
    }
  });

  $("foto").addEventListener("change", alElegirArchivo);
  $("archivo").addEventListener("change", alElegirArchivo);
  $("partida-gasto").addEventListener("change", actualizarCampoHoras);
  $("form-datos").addEventListener("submit", enviarFormulario);
  $("descartar").addEventListener("click", descartar);
  $("volver").addEventListener("click", mostrarPantalla);

  // Obras existentes para el gasto sin solicitud; se elige, no se escribe
  async function cargarObras() {
    try {
      const obras = await llamar("/catalogo/obras");
      $("obra-gasto").append(...obras.map((o) => {
        const opcion = document.createElement("option");
        opcion.value = o.id;
        opcion.textContent = o.nombre + " · " + o.id;
        return opcion;
      }));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  const obrasListas = cargarObras();
  mostrarPantalla();
})();
