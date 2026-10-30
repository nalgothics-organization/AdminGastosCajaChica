// Tablero de inicio: resume todas las obras con los datos que ya existen en la API
// (saldos, solicitudes y comprobantes). Si la base viene del seed, aquí se ven los datos de ejemplo.
(function () {
  "use strict";

  const moneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
  const fechaCorta = new Intl.DateTimeFormat("es-MX", { day: "numeric", month: "short" });
  const MAXIMO_MOVIMIENTOS = 6;

  const suma = (lista, campo) => lista.reduce((total, fila) => total + Number(fila[campo]), 0);
  const porcentaje = (parte, total) => (total > 0 ? Math.round((parte / total) * 1000) / 10 : 0);

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

  async function pedir(ruta) {
    const respuesta = await fetch("/api" + ruta);
    if (!respuesta.ok) {
      throw new Error("No se pudo leer " + ruta);
    }
    return respuesta.json();
  }

  const pastilla = (texto, color) => el("span", "pastilla " + color, texto);

  function indicador(titulo, valor, nota, avance, color, destacado) {
    const relleno = el("span");
    relleno.style.width = Math.min(avance, 100) + "%";
    return el("div", "tarjeta kpi" + (destacado ? " destacado" : ""), null,
      el("small", "", titulo),
      el("div", "kpi-valor mono", moneda.format(valor)),
      el("small", "", nota),
      el("div", "barra " + color, null, relleno));
  }

  function indicadores(saldos) {
    const autorizado = suma(saldos, "autorizado");
    const comprobado = suma(saldos, "comprobado");
    const pendiente = suma(saldos, "pendiente_autorizacion");
    return el("div", "kpis", null,
      indicador("Autorizado", autorizado, saldos.length + " obra(s) con fondo", 100, "azul"),
      indicador("Comprobado", comprobado, porcentaje(comprobado, autorizado) + "% de lo autorizado",
        porcentaje(comprobado, autorizado), "verde"),
      indicador("Saldo disponible", autorizado - comprobado, "Autorizado menos comprobado",
        porcentaje(autorizado - comprobado, autorizado), "azul"),
      indicador("Por autorizar", pendiente, suma(saldos, "solicitudes_pendientes") + " solicitud(es) en espera",
        100, "morado", true));
  }

  function estatus(solicitud) {
    if (solicitud.estado === "Aprobado") {
      return pastilla("Aprobada", "verde");
    }
    if (solicitud.estado === "Rechazado") {
      return pastilla("Rechazada", "rojo");
    }
    return pastilla("En " + solicitud.nivel_autorizacion.toLowerCase(), "ambar");
  }

  function comprobacion(solicitud, comprobantes) {
    if (solicitud.estado !== "Aprobado") {
      return el("span", "nota", "—");
    }
    const cerrado = comprobantes.find((c) => c.solicitud_id === solicitud.id && c.estado !== "Borrador");
    if (!cerrado) {
      return pastilla("Por comprobar", "ambar");
    }
    return cerrado.estado === "Comprobado" ? pastilla("Comprobada", "verde") : pastilla("En revisión", "morado");
  }

  function tabla(solicitudes, comprobantes) {
    const encabezado = ["Folio", "Concepto", "Etapa", "Monto", "Fecha", "Estatus", "Comprobación"];
    const recientes = solicitudes.slice().reverse().slice(0, MAXIMO_MOVIMIENTOS);
    const filas = recientes.map((s) =>
      el("tr", "", null,
        el("td", "mono", s.folio),
        el("td", "fuerte", s.concepto),
        el("td", "", s.etapa_construccion),
        el("td", "mono derecha", moneda.format(s.monto_solicitado)),
        el("td", "", fechaCorta.format(new Date(s.created_at))),
        el("td", "", null, estatus(s)),
        el("td", "", null, comprobacion(s, comprobantes))));
    return el("div", "tabla-contenedor", null,
      el("table", "tabla", null,
        el("thead", "", null, el("tr", "", null, ...encabezado.map((t) => el("th", "", t)))),
        el("tbody", "", null, ...filas)));
  }

  function pendientes(saldos, solicitudes, comprobantes) {
    const alertas = [];
    const enEspera = solicitudes.filter((s) => s.estado === "Pendiente");
    if (enEspera.length) {
      const monto = moneda.format(suma(saldos, "pendiente_autorizacion"));
      alertas.push(["ambar", enEspera.length + " solicitud(es)", " esperan decisión por " + monto + "."]);
    }
    const sinComprobar = solicitudes.filter((s) => s.estado === "Aprobado"
      && !comprobantes.some((c) => c.solicitud_id === s.id && c.estado !== "Borrador"));
    if (sinComprobar.length) {
      const folios = sinComprobar.map((s) => s.folio).join(", ");
      alertas.push(["azul", sinComprobar.length + " aprobada(s)", " sin comprobar: " + folios + "."]);
    }
    const borradores = comprobantes.filter((c) => c.estado === "Borrador");
    if (borradores.length) {
      alertas.push(["morado", borradores.length + " foto(s)", " por completar con sus datos."]);
    }
    const sinSolicitud = suma(saldos, "gasto_sin_solicitud");
    if (sinSolicitud > 0) {
      alertas.push(["ambar", moneda.format(sinSolicitud), " pagados sin solicitud: reembolso pendiente."]);
    }
    const contenido = alertas.length
      ? alertas.map(([color, fuerte, resto]) => el("p", "alerta " + color, null, el("strong", "", fuerte), resto))
      : [el("p", "nota", "Sin pendientes por hoy.")];
    return el("aside", "panel", null, el("h2", "", "Pendientes de hoy"), ...contenido);
  }

  async function cargar() {
    const contenedor = document.getElementById("tablero");
    try {
      const [saldos, solicitudes, comprobantes] = await Promise.all(
        [pedir("/saldos"), pedir("/solicitudes"), pedir("/comprobantes")]);
      contenedor.replaceChildren(
        indicadores(saldos),
        el("div", "dos-columnas", null, tabla(solicitudes, comprobantes), pendientes(saldos, solicitudes, comprobantes)));
    } catch (e) {
      contenedor.replaceChildren(el("p", "nota", "No se pudo cargar el resumen: " + e.message));
    }
  }

  if (document.getElementById("tablero")) {
    cargar();
  }
})();
