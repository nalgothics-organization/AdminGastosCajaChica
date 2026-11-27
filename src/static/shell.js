// Estructura común de las pantallas (barra lateral, barra superior y pestañas de Caja chica).
// Envuelve el <main> de cada página. Muestra a quien inició sesión, solo las pestañas de su rol
// y bloquea las pantallas que su rol no puede usar (RF15/HU20). Requiere sesion.js.
(function () {
  "use strict";

  const Sesion = window.Sesion;
  const usuario = Sesion.actual();
  if (!usuario) {
    return; // sesion.js ya redirigió al inicio de sesión
  }

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
    hijos.forEach((hijo) => hijo && nodo.append(hijo));
    return nodo;
  }

  function barraLateral() {
    const secciones = SECCIONES.map(([titulo, detalle, activa]) =>
      el("div", "lateral-item" + (activa ? " activo" : ""), null, el("strong", "", titulo), el("small", "", detalle)));
    const obra = usuario.obra_id
      ? el("div", "obra-activa", null, el("small", "", "TU OBRA"), el("strong", "mono", usuario.obra_id))
      : el("div", "obra-activa", null, el("small", "", "ALCANCE"), el("strong", "", "Todas las obras"));
    return el("aside", "lateral", null,
      el("div", "marca", null,
        el("span", "marca-logo", "CM"),
        el("div", "", null, el("strong", "", "CIMAS ERP"), el("small", "", "CONTROL DE OBRA"))),
      obra,
      el("small", "lateral-titulo", "MENÚ PRINCIPAL"),
      ...secciones,
      el("div", "lateral-pie", null, el("strong", "", "CIMAS ERP v2.4"), el("small", "", "Control Integral de Obra")));
  }

  function barraSuperior() {
    const salir = el("button", "secundario salir", "Cerrar sesión");
    salir.type = "button";
    salir.addEventListener("click", () => {
      Sesion.cerrar();
      location.replace("login.html");
    });
    const cuenta = el("a", "usuario", null,
      el("div", "", null, el("strong", "", usuario.nombre), el("small", "", usuario.rol + " · " + usuario.usuario)),
      el("span", "avatar", Sesion.iniciales(usuario.nombre)));
    cuenta.href = "cuenta.html";
    cuenta.title = "Mi cuenta";
    return el("header", "superior", null,
      el("div", "proyecto", null, el("small", "", "MÓDULO"), el("strong", "", "Caja chica y gastos")),
      el("div", "buscador", "Buscar globalmente (actividades, personal, incidencias)..."),
      cuenta,
      salir);
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
    Sesion.PANTALLAS.filter(([, , roles]) => roles.includes(usuario.rol)).forEach(([ruta, texto]) => {
      const enlace = el("a", "", texto);
      enlace.href = ruta;
      if (ruta === Sesion.paginaActual()) {
        enlace.setAttribute("aria-current", "page");
      }
      menu.append(enlace);
    });
    return menu;
  }

  // Si el rol no puede usar la pantalla, se oculta su contenido y se muestra un aviso en su lugar
  function sinPermiso() {
    return el("section", "", null,
      el("section", "panel", null,
        el("h1", "", "Esta pantalla no es para tu rol"),
        el("p", "nota", "Iniciaste sesión como " + usuario.rol + ". Usa las pestañas de arriba para ir a tus apartados."),
        el("div", "acciones inicio", null, Object.assign(el("a", "boton-enlace", "Ir a mi inicio"), {
          href: Sesion.inicioDe(usuario),
        }))));
  }

  const principal = document.querySelector("main");
  const permitido = Sesion.puedeVer(Sesion.paginaActual(), usuario);
  if (!permitido) {
    principal.hidden = true;
  }
  const contenido = el("div", "contenido", null, modulos(), pestanas(), permitido ? null : sinPermiso(), principal);
  const aplicacion = el("div", "aplicacion", null, barraLateral(), el("div", "columna", null, barraSuperior(), contenido));
  document.body.prepend(aplicacion);

  // Si el usuario se dio de baja mientras tenía la sesión abierta, se le saca
  fetch("/api/usuarios/" + encodeURIComponent(usuario.usuario))
    .then((respuesta) => {
      if (respuesta.status === 404) {
        Sesion.cerrar();
        Sesion.irAlLogin();
      }
    })
    .catch(() => {
      // Sin conexión se sigue con la sesión guardada
    });
})();
