// Pantalla de un comprobante enviado: la foto y los datos que leyó el OCR (RF11/HU11).
(function () {
  "use strict";

  const API = "/api";
  const $ = (id) => document.getElementById(id);
  const DATOS = [
    ["proveedor", "Proveedor"],
    ["fecha_gasto", "Fecha"],
    ["monto_comprobado", "Monto"],
    ["tipo", "Tipo"],
  ];
  const TIPOS = { factura: "Factura", ticket: "Ticket", nota_simple: "Nota simple" };

  // Crea un elemento con texto seguro (nunca interpreta HTML de los datos)
  function el(etiqueta, clase, texto, ...hijos) {
    const nodo = document.createElement(etiqueta);
    if (clase) {
      nodo.className = clase;
    }
    if (texto) {
      nodo.textContent = texto;
    }
    hijos.forEach((hijo) => nodo.append(hijo));
    return nodo;
  }

  function formatear(campo, valor) {
    if (campo === "monto_comprobado") {
      return "$" + Number(valor).toLocaleString("es-MX", { minimumFractionDigits: 2, maximumFractionDigits: 2 });
    }
    if (campo === "fecha_gasto") {
      return new Date(valor + "T00:00:00").toLocaleDateString("es-MX", { day: "numeric", month: "long", year: "numeric" });
    }
    if (campo === "tipo") {
      return TIPOS[valor] || valor;
    }
    return valor;
  }

  function mostrarMensaje(texto) {
    const mensaje = $("mensaje");
    mensaje.textContent = texto;
    mensaje.hidden = false;
  }

  // Cada dato se muestra como leído, confirmado o por completar
  function filaDeDato(rotulo, valor, etiqueta) {
    const estado = valor === null || valor === undefined || valor === ""
      ? el("span", "pastilla ambar", "Por completar")
      : el("span", "pastilla verde", etiqueta);
    const texto = valor ? el("strong", "dato-valor", valor) : el("span", "dato-valor vacio", "—");
    return el("li", "", null, el("span", "dato-rotulo", rotulo), texto, estado);
  }

  function pintarDatos(comprobante) {
    const confirmado = Boolean(comprobante.datos);
    const fuente = comprobante.datos || comprobante.lectura || {};
    const etiqueta = confirmado ? "Confirmado" : "Leído";
    $("datos-leidos").replaceChildren(...DATOS.map(([campo, rotulo]) =>
      filaDeDato(rotulo, fuente[campo] ? formatear(campo, fuente[campo]) : null, etiqueta)));

    const resumen = $("resumen-lectura");
    if (confirmado) {
      resumen.textContent = "Estos datos ya fueron confirmados.";
    } else if (!comprobante.lectura) {
      resumen.textContent = "No se leyeron datos de esta foto. Complétalos a mano.";
    } else {
      const faltan = comprobante.lectura.faltantes.length;
      resumen.textContent = faltan === 0
        ? "Se leyeron los 4 datos. Revísalos y confírmalos."
        : "Se leyeron " + (DATOS.length - faltan) + " de " + DATOS.length + " datos. Lo que falta queda por completar.";
    }

    const renglones = comprobante.lectura ? comprobante.lectura.renglones : [];
    $("texto-leido").hidden = renglones.length === 0;
    $("renglones").textContent = renglones.join("\n");
  }

  function pintar(comprobante) {
    $("estado").textContent = comprobante.estado === "Borrador"
      ? "Por completar: confirma los datos para enviarlo a revisión."
      : "Estado: " + comprobante.estado + ".";
    const foto = $("foto-comprobante");
    foto.addEventListener("error", () => { foto.hidden = true; });
    foto.src = API + "/comprobantes/" + encodeURIComponent(comprobante.id) + "/imagen";
    pintarDatos(comprobante);

    const completar = $("completar");
    completar.hidden = comprobante.estado !== "Borrador";
    completar.href = "index.html?abrir=" + encodeURIComponent(comprobante.id);
    $("vista").hidden = false;
  }

  async function cargar() {
    const id = new URLSearchParams(location.search).get("id");
    if (!id) {
      mostrarMensaje("No se indicó qué comprobante mostrar.");
      return;
    }
    try {
      const respuesta = await fetch(API + "/comprobantes/" + encodeURIComponent(id));
      if (!respuesta.ok) {
        mostrarMensaje(respuesta.status === 404 ? "Ese comprobante ya no existe." : "No se pudo cargar el comprobante.");
        return;
      }
      pintar(await respuesta.json());
    } catch (e) {
      mostrarMensaje("No se pudo cargar el comprobante. Revisa tu conexión.");
    }
  }

  cargar();
})();
