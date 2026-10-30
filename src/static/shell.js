// Estructura común de las pantallas (barra lateral, barra superior y pestañas de Caja chica).
// Envuelve el <main> de cada página; los ids y la lógica de cada pantalla no se tocan.
(function () {
  "use strict";

  const PESTANAS = [
    ["index.html", "Mi caja chica"],
    ["solicitud.html", "Nueva solicitud"],
    ["autorizacion.html", "Autorizaciones"],
    ["saldos.html", "Saldos por obra"],
  ];
  const MODULOS = [
    "Dashboard + IA", "Centro de Costo + IA", "Centro de Gastos + IA", "Inventarios + IA",
    "Caja Chica + IA", "Estimaciones + IA", "Documental + IA",
  ];
  const SECCIONES = [
    ["Planner", "Cronograma, Gantt y Plantilla", false],
    ["Ejecución (campo)", "Bitácora, Fotos HD y Asistencia", false],
    ["Administración", "Costos, Gastos, Almacén y Cobranza", true],
    ["Configuración", "General, Roles, Usuarios y Reglas", false],
  ];

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

  function barraLateral() {
    const secciones = SECCIONES.map(([titulo, detalle, activa]) => {
      const item = el("div", "lateral-item" + (activa ? " activo" : ""), null,
        el("strong", "", titulo), el("small", "", detalle));
      return item;
    });
    return el("aside", "lateral", null,
      el("div", "marca", null,
        el("span", "marca-logo", "CM"),
        el("div", "", null, el("strong", "", "CIMAS ERP"), el("small", "", "CONTROL DE OBRA"))),
      el("div", "obra-activa", null,
        el("small", "", "OBRA ACTIVA"), el("strong", "", "Torre Residencial Cimas Norte"),
        el("small", "mono", "CIM-2026-N1")),
      el("small", "lateral-titulo", "MENÚ PRINCIPAL"),
      ...secciones,
      el("div", "lateral-pie", null, el("strong", "", "CIMAS ERP v2.4"), el("small", "", "Control Integral de Obra")));
  }

  function barraSuperior() {
    return el("header", "superior", null,
      el("div", "proyecto", null, el("small", "", "PROYECTO"), el("strong", "", "Torre Residencial Cimas Norte")),
      el("div", "buscador", "Buscar globalmente (actividades, personal, incidencias)..."),
      el("div", "usuario", null,
        el("div", "", null, el("strong", "", "Arq. Roberto Garza"), el("small", "", "Residente General")),
        el("span", "avatar", "RG")));
  }

  function modulos() {
    const barra = el("nav", "modulos");
    MODULOS.forEach((nombre) => {
      barra.append(el("span", "modulo" + (nombre.startsWith("Caja Chica") ? " activo" : ""), nombre));
    });
    barra.append(el("span", "modulo ia", "IA CIMAS"));
    return barra;
  }

  function pestanas() {
    const menu = el("nav", "menu");
    PESTANAS.forEach(([ruta, texto]) => {
      const enlace = el("a", "", texto);
      enlace.href = ruta;
      menu.append(enlace);
    });
    return menu;
  }

  const principal = document.querySelector("main");
  const contenido = el("div", "contenido", null, modulos(), pestanas(), principal);
  const aplicacion = el("div", "aplicacion", null, barraLateral(), el("div", "columna", null, barraSuperior(), contenido));
  document.body.prepend(aplicacion);
})();
