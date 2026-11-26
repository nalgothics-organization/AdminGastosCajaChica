// Utilidades compartidas por las pantallas del prototipo (solicitud, autorización y saldos).
(function () {
  "use strict";

  const API = "/api";
  const CLAVE_RESIDENTE = "cajaChica.residente";
  const formatoMoneda = new Intl.NumberFormat("es-MX", { style: "currency", currency: "MXN" });
  // Quién absorbe el gasto (RF14/HU15)
  const CLASIFICACIONES = {
    cobrable_cliente: "Cobrable al cliente",
    fondo_contingencia: "Fondo de contingencia",
  };

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

  function enviarJson(metodo, cuerpo) {
    return { method: metodo, headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) };
  }

  function avisar(mensaje, esError) {
    const aviso = document.getElementById("aviso");
    aviso.textContent = mensaje;
    aviso.classList.toggle("error", Boolean(esError));
    aviso.hidden = false;
    clearTimeout(avisar.temporizador);
    avisar.temporizador = setTimeout(() => { aviso.hidden = true; }, 5000);
  }

  // Crea un elemento con texto seguro (nunca interpreta HTML de los datos)
  function el(etiqueta, atributos, ...hijos) {
    const nodo = document.createElement(etiqueta);
    Object.entries(atributos || {}).forEach(([clave, valor]) => {
      if (clave === "texto") {
        nodo.textContent = valor;
      } else if (clave in nodo) {
        nodo[clave] = valor;
      } else {
        nodo.setAttribute(clave, valor);
      }
    });
    hijos.flat().filter(Boolean).forEach((hijo) => nodo.append(hijo));
    return nodo;
  }

  function leer(clave) {
    try {
      return localStorage.getItem(clave) || "";
    } catch (e) {
      return "";
    }
  }

  function guardar(clave, valor) {
    try {
      localStorage.setItem(clave, valor);
    } catch (e) {
      // Sin almacenamiento local el dato se vuelve a pedir en la siguiente visita
    }
  }

  function marcarPaginaActual() {
    const actual = location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".menu a").forEach((enlace) => {
      if (enlace.getAttribute("href") === actual) {
        enlace.setAttribute("aria-current", "page");
      }
    });
  }

  function etiquetaEstado(estado) {
    const clase = estado === "Aprobado" ? "aprobado" : estado === "Rechazado" ? "rechazado" : "";
    return el("span", { className: "etiqueta " + clase, texto: estado });
  }

  window.Caja = {
    CLAVE_RESIDENTE,
    CLASIFICACIONES,
    llamar,
    enviarJson,
    avisar,
    el,
    leer,
    guardar,
    etiquetaEstado,
    dinero: (valor) => formatoMoneda.format(Number(valor)),
  };

  document.addEventListener("DOMContentLoaded", marcarPaginaActual);
})();
