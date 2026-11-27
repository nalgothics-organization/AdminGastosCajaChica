// Comprobantes para contabilidad, administración y dirección: revisión, historial y correcciones
// por ajuste o reverso que referencian al original sin modificarlo (RF07/HU07, AGENTS.md §8).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, dinero, CLASIFICACIONES } = window.Caja;
  const $ = (id) => document.getElementById(id);
  const CERRADOS = ["Comprobado", "Revisión contabilidad"];
  const TIPOS = { factura: "Factura", ticket: "Ticket", nota_simple: "Nota simple" };
  const REGISTROS = { original: "Original", ajuste: "Ajuste", reverso: "Reverso" };
  const COLORES = { "Comprobado": "verde", "Revisión contabilidad": "morado", "Borrador": "ambar" };

  let comprobantes = [];
  let usuarios = {};
  let elegido = null;

  const pastilla = (texto, color) => el("span", { className: "pastilla " + (color || ""), texto });
  const fecha = (valor) => new Date(valor).toLocaleString("es-MX", { dateStyle: "medium", timeStyle: "short" });

  function nombreDe(usuario) {
    return usuarios[usuario] ? usuarios[usuario].nombre : usuario;
  }

  function correccionesDe(id) {
    return comprobantes.filter((c) => c.comprobante_origen_id === id);
  }

  function filtrados() {
    const estado = $("filtro-estado").value;
    const residente = $("filtro-residente").value;
    const obra = $("filtro-obra").value;
    const registro = $("filtro-registro").value;
    return comprobantes
      .filter((c) => (!estado || c.estado === estado)
        && (!residente || c.solicitante_id === residente)
        && (!obra || c.obra_id === obra)
        && (!registro || c.tipo_registro === registro))
      .sort((a, b) => b.created_at.localeCompare(a.created_at));
  }

  function kpi(titulo, valor, detalle, destacado) {
    return el("div", { className: "panel kpi" + (destacado ? " destacado" : "") },
      el("small", { texto: titulo }), el("p", { className: "kpi-valor", texto: valor }), el("small", { texto: detalle }));
  }

  function pintarKpis() {
    const enRevision = comprobantes.filter((c) => c.estado === "Revisión contabilidad" && c.tipo_registro !== "reverso");
    const borradores = comprobantes.filter((c) => c.estado === "Borrador");
    const correcciones = comprobantes.filter((c) => c.tipo_registro !== "original");
    const montoRevision = enRevision.reduce((t, c) => t + Number(c.datos ? c.datos.monto_comprobado : 0), 0);
    $("kpis").replaceChildren(
      kpi("En revisión", String(enRevision.length), dinero(montoRevision) + " por revisar", true),
      kpi("Borradores", String(borradores.length), "fotos que el residente no ha completado"),
      kpi("Correcciones", String(correcciones.length), "ajustes y reversos registrados"),
      kpi("Total", String(comprobantes.length), "comprobantes activos")
    );
  }

  function fila(c) {
    const ver = el("button", { type: "button", className: "secundario", texto: "Ver" });
    ver.addEventListener("click", () => abrir(c.id));
    const monto = c.datos ? dinero(c.datos.monto_comprobado) : "—";
    return el("tr", { className: elegido === c.id ? "elegida" : "" },
      el("td", { texto: fecha(c.created_at) }),
      el("td", { texto: nombreDe(c.solicitante_id) }),
      el("td", { texto: (c.obra_id || "Sin obra") + (c.partida_categoria ? " · " + c.partida_categoria : "") }),
      el("td", {}, pastilla(REGISTROS[c.tipo_registro], c.tipo_registro === "original" ? "" : "azul")),
      el("td", { texto: c.datos ? TIPOS[c.datos.tipo] : "—" }),
      el("td", { className: "derecha fuerte" + (c.tipo_registro === "reverso" ? " negativo" : ""), texto: monto }),
      el("td", {}, pastilla(c.estado, COLORES[c.estado])),
      el("td", {}, ver));
  }

  function pintarTabla() {
    const lista = filtrados();
    $("filas").replaceChildren(...lista.map(fila));
    $("vacio").hidden = lista.length > 0;
  }

  function dato(rotulo, valor) {
    return [el("dt", { texto: rotulo }), el("dd", { texto: valor || "—" })];
  }

  function pintarDatos(c) {
    const d = c.datos || {};
    const lectura = c.lectura;
    $("detalle-datos").replaceChildren(
      ...dato("Residente", nombreDe(c.solicitante_id) + " (" + c.solicitante_id + ")"),
      ...dato("Estado", c.estado + (c.cierre_automatico ? " · cerrado solo al leerse completo" : "")),
      ...dato("Registro", REGISTROS[c.tipo_registro]),
      ...dato("Solicitud", c.solicitud_id ? "Vinculada" : "Pagado sin solicitud (reembolso)"),
      ...dato("Obra", c.obra_id),
      ...dato("Etapa · partida", [c.etapa_construccion, c.partida_categoria].filter(Boolean).join(" · ")),
      ...dato("Se paga con", c.clasificacion ? CLASIFICACIONES[c.clasificacion] : ""),
      ...dato("Tipo", d.tipo ? TIPOS[d.tipo] : ""),
      ...dato("Monto", d.monto_comprobado ? dinero(d.monto_comprobado) : ""),
      ...dato("Fecha del gasto", d.fecha_gasto),
      ...dato("Proveedor", d.proveedor),
      ...dato("Concepto", d.concepto),
      ...(d.horas ? dato("Horas", d.horas + " de " + d.unidad_horas) : []),
      ...(c.motivo_correccion ? dato("Motivo", c.motivo_correccion) : []),
      ...(lectura ? dato("Lectura OCR", "confianza " + Math.round((lectura.confianza || 0) * 100) + "%"
        + (lectura.faltantes.length ? " · faltó " + lectura.faltantes.join(", ") : " · completa")) : [])
    );
  }

  function pintarHistorial(c) {
    const origen = c.comprobante_origen_id ? comprobantes.find((o) => o.id === c.comprobante_origen_id) : null;
    const correcciones = correccionesDe(c.id);
    const elementos = [];
    if (origen) {
      const enlace = el("button", { type: "button", className: "secundario", texto: "Ver el comprobante original" });
      enlace.addEventListener("click", () => abrir(origen.id));
      elementos.push(el("p", { className: "nota", texto: "Corrige al comprobante del " + fecha(origen.created_at) + "." }), enlace);
    }
    if (correcciones.length) {
      elementos.push(el("h3", { texto: "Correcciones de este comprobante" }), el("ul", {}, correcciones.map((k) => {
        const boton = el("button", { type: "button", className: "secundario",
          texto: REGISTROS[k.tipo_registro] + " · " + fecha(k.created_at) + (k.datos && k.tipo_registro === "ajuste"
            ? " · " + dinero(k.datos.monto_comprobado) : "") });
        boton.addEventListener("click", () => abrir(k.id));
        return el("li", {}, boton);
      })));
    }
    $("detalle-historial").replaceChildren(...elementos);
  }

  // Solo un original cerrado y sin reverso admite corrección (mismas reglas que el servidor)
  function motivoSinCorreccion(c) {
    if (!CERRADOS.includes(c.estado)) {
      return "Un borrador lo completa el residente; no se corrige con ajuste.";
    }
    if (c.tipo_registro !== "original") {
      return "Las correcciones se registran sobre el comprobante original.";
    }
    if (correccionesDe(c.id).some((k) => k.tipo_registro === "reverso")) {
      return "Este comprobante ya fue reversado.";
    }
    return "";
  }

  function prepararCorreccion(c) {
    const motivo = motivoSinCorreccion(c);
    $("form-correccion").hidden = Boolean(motivo);
    $("sin-correccion").hidden = !motivo;
    $("sin-correccion").textContent = motivo;
    if (motivo) {
      return;
    }
    const form = $("form-correccion");
    form.reset();
    const d = c.datos || {};
    if (d.tipo) {
      form.querySelector('input[name="tipo"][value="' + d.tipo + '"]').checked = true;
    }
    form.elements.monto_comprobado.value = d.monto_comprobado || "";
    form.elements.fecha_gasto.value = d.fecha_gasto || "";
    form.elements.proveedor.value = d.proveedor || "";
    form.elements.concepto.value = d.concepto || "";
    form.elements.horas.value = d.horas || "";
    if (d.unidad_horas) {
      form.elements.unidad_horas.value = d.unidad_horas;
    }
    $("aj-campo-horas").hidden = !c.requiere_horas;
    alternarCampos();
  }

  function abrir(id) {
    const c = comprobantes.find((x) => x.id === id);
    if (!c) {
      return;
    }
    elegido = id;
    $("detalle-titulo").textContent = REGISTROS[c.tipo_registro] + " de " + nombreDe(c.solicitante_id)
      + " · " + fecha(c.created_at);
    const foto = $("detalle-foto");
    foto.hidden = false;
    foto.onerror = () => { foto.hidden = true; };
    foto.src = "/api/comprobantes/" + encodeURIComponent(c.id) + "/imagen";
    $("detalle-enlace").href = "comprobante.html?id=" + encodeURIComponent(c.id);
    pintarDatos(c);
    pintarHistorial(c);
    prepararCorreccion(c);
    $("detalle").hidden = false;
    pintarTabla();
    $("detalle").scrollIntoView({ behavior: "smooth", block: "start" });
  }

  function alternarCampos() {
    const reverso = $("form-correccion").querySelector('input[name="tipo_registro"]:checked').value === "reverso";
    $("campos-ajuste").hidden = reverso;
  }

  function leerCorreccion() {
    const form = $("form-correccion");
    const tipoRegistro = form.querySelector('input[name="tipo_registro"]:checked').value;
    const cuerpo = { tipo_registro: tipoRegistro, motivo: form.elements.motivo.value.trim() };
    if (tipoRegistro === "ajuste") {
      const tipo = form.querySelector('input[name="tipo"]:checked');
      const conHoras = !$("aj-campo-horas").hidden;
      cuerpo.datos = {
        tipo: tipo ? tipo.value : null,
        monto_comprobado: form.elements.monto_comprobado.value || null,
        fecha_gasto: form.elements.fecha_gasto.value || null,
        proveedor: form.elements.proveedor.value,
        concepto: form.elements.concepto.value,
        horas: conHoras ? form.elements.horas.value || null : null,
        unidad_horas: conHoras ? form.elements.unidad_horas.value : null,
      };
    }
    return cuerpo;
  }

  async function registrarCorreccion(evento) {
    evento.preventDefault();
    const cuerpo = leerCorreccion();
    if (cuerpo.tipo_registro === "reverso"
      && !confirm("El reverso anula el comprobante y su monto deja de contar en los saldos. ¿Continuar?")) {
      return;
    }
    try {
      const nuevo = await llamar("/comprobantes/" + elegido + "/ajustes", enviarJson("POST", cuerpo));
      avisar((cuerpo.tipo_registro === "ajuste" ? "Ajuste" : "Reverso") + " registrado; queda en revisión de contabilidad.");
      await cargar();
      abrir(nuevo.id);
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function llenarFiltro(select, opciones) {
    const actual = select.value;
    select.replaceChildren(select.options[0], ...opciones.map(([valor, texto]) => el("option", { value: valor, texto })));
    select.value = actual;
  }

  async function cargar() {
    try {
      const [lista, todos] = await Promise.all([
        llamar("/comprobantes"),
        llamar("/usuarios"),
      ]);
      comprobantes = lista;
      usuarios = Object.fromEntries(todos.map((u) => [u.usuario, u]));
      const solicitantes = [...new Set(lista.map((c) => c.solicitante_id))].sort();
      const obras = [...new Set(lista.map((c) => c.obra_id).filter(Boolean))].sort();
      llenarFiltro($("filtro-residente"), solicitantes.map((u) => [u, nombreDe(u) + " · " + u]));
      llenarFiltro($("filtro-obra"), obras.map((o) => [o, o]));
      pintarKpis();
      pintarTabla();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  ["filtro-estado", "filtro-residente", "filtro-obra", "filtro-registro"].forEach((id) =>
    $(id).addEventListener("change", pintarTabla));
  $("form-correccion").addEventListener("change", (e) => {
    if (e.target.name === "tipo_registro") {
      alternarCampos();
    }
  });
  $("form-correccion").addEventListener("submit", registrarCorreccion);
  $("cerrar-detalle").addEventListener("click", () => {
    elegido = null;
    $("detalle").hidden = true;
    pintarTabla();
  });

  cargar();
})();
