// Sesión del prototipo (RF15/HU20): quién inició sesión, qué rol tiene y qué pantallas puede abrir.
// Se carga antes que shell.js en todas las pantallas. Los datos viven en el navegador; la API
// vuelve a comprobar el rol en cada acción (solicitar, comprobar, autorizar).
(function () {
  "use strict";

  const CLAVE_SESION = "cajaChica.sesion";
  // Claves que usaban las pantallas antes del inicio de sesión; se llenan con el usuario de la sesión
  const CLAVE_RESIDENTE = "cajaChica.residente";
  const CLAVE_AUTORIZADOR = "cajaChica.autorizador";

  const ROLES = {
    RESIDENTE: "Residente de obra",
    ADMINISTRACION: "Administración",
    DIRECCION: "Dirección",
    CONTABILIDAD: "Contabilidad",
  };
  const TODOS = Object.values(ROLES);
  const DECIDEN = [ROLES.ADMINISTRACION, ROLES.DIRECCION];

  // Pestañas en orden: archivo, texto y roles que la ven
  const PANTALLAS = [
    ["index.html", "Mi caja chica", [ROLES.RESIDENTE]],
    ["solicitud.html", "Nueva solicitud", [ROLES.RESIDENTE]],
    ["autorizacion.html", "Autorizaciones", DECIDEN],
    ["revision.html", "Comprobantes", [ROLES.CONTABILIDAD, ...DECIDEN]],
    ["saldos.html", "Saldos por obra", TODOS],
    ["obras.html", "Obras", DECIDEN],
    ["usuarios.html", "Usuarios", DECIDEN],
    ["cuenta.html", "Mi cuenta", TODOS],
    ["pruebas.html", "Guía de pruebas", TODOS],
  ];
  // Pantallas que no son pestaña pero también requieren sesión
  const OTRAS = { "comprobante.html": TODOS };

  const INICIO_POR_ROL = {
    [ROLES.RESIDENTE]: "index.html",
    [ROLES.ADMINISTRACION]: "autorizacion.html",
    [ROLES.DIRECCION]: "autorizacion.html",
    [ROLES.CONTABILIDAD]: "revision.html",
  };

  function leer(clave) {
    try {
      return localStorage.getItem(clave) || "";
    } catch (e) {
      return "";
    }
  }

  function escribir(clave, valor) {
    try {
      if (valor) {
        localStorage.setItem(clave, valor);
      } else {
        localStorage.removeItem(clave);
      }
    } catch (e) {
      // Sin almacenamiento local la sesión dura solo mientras la página esté abierta
    }
  }

  let actual = null;
  try {
    actual = JSON.parse(leer(CLAVE_SESION) || "null");
  } catch (e) {
    actual = null;
  }

  function sincronizarClaves(usuario) {
    const esResidente = usuario && usuario.rol === ROLES.RESIDENTE;
    const decide = usuario && DECIDEN.includes(usuario.rol);
    escribir(CLAVE_RESIDENTE, esResidente ? usuario.usuario : "");
    escribir(CLAVE_AUTORIZADOR, decide ? usuario.usuario : "");
  }

  // Solo se guardan los datos públicos que devuelve la API (nunca la contraseña)
  function iniciar(usuario) {
    actual = {
      id: usuario.id,
      usuario: usuario.usuario,
      nombre: usuario.nombre,
      email: usuario.email,
      rol: usuario.rol,
      obra_id: usuario.obra_id || null,
    };
    escribir(CLAVE_SESION, JSON.stringify(actual));
    sincronizarClaves(actual);
    return actual;
  }

  function cerrar() {
    actual = null;
    escribir(CLAVE_SESION, "");
    sincronizarClaves(null);
  }

  function paginaActual() {
    return location.pathname.split("/").pop() || "index.html";
  }

  function rolesDe(pagina) {
    const pantalla = PANTALLAS.find(([archivo]) => archivo === pagina);
    return pantalla ? pantalla[2] : OTRAS[pagina] || null;
  }

  function puedeVer(pagina, usuario) {
    const roles = rolesDe(pagina);
    return Boolean(usuario) && (!roles || roles.includes(usuario.rol));
  }

  function inicioDe(usuario) {
    return (usuario && INICIO_POR_ROL[usuario.rol]) || "login.html";
  }

  function iniciales(nombre) {
    return (nombre || "?").split(/\s+/).filter(Boolean).slice(0, 2).map((p) => p[0].toUpperCase()).join("");
  }

  function irAlLogin() {
    const volver = paginaActual() + location.search;
    location.replace("login.html?volver=" + encodeURIComponent(volver));
  }

  window.Sesion = {
    ROLES,
    PANTALLAS,
    actual: () => actual,
    usuario: () => (actual ? actual.usuario : ""),
    iniciar,
    cerrar,
    paginaActual,
    puedeVer,
    inicioDe,
    iniciales,
    irAlLogin,
  };

  // Sin sesión no se muestra ninguna pantalla del módulo
  if (paginaActual() !== "login.html" && !actual) {
    irAlLogin();
  } else if (actual) {
    sincronizarClaves(actual);
  }
})();
