// Inicio de sesión y registro de cuenta (RF15/HU20).
(function () {
  "use strict";

  const Sesion = window.Sesion;
  const $ = (id) => document.getElementById(id);
  // Los mismos que crea src/seed.py; la contraseña nunca se muestra aquí
  const DEMO = [
    ["RESIDENTE-PAU", "Paula Rivas", "Residente · OBRA-NORTE-01"],
    ["RESIDENTE-JP", "Juan Pablo Ortiz", "Residente · OBRA-SUR-02"],
    ["RESIDENTE-LUIS", "Luis Torres", "Residente · OBRA-NORTE-01"],
    ["ADMIN-LAURA", "Laura Méndez", "Administración"],
    ["DIR-CARLOS", "Carlos Ruiz", "Dirección"],
    ["CONT-SOFIA", "Sofía Navarro", "Contabilidad"],
  ];

  function avisar(mensaje, esError) {
    const aviso = $("aviso");
    aviso.textContent = mensaje;
    aviso.classList.toggle("error", Boolean(esError));
    aviso.hidden = false;
  }

  async function llamar(ruta, cuerpo) {
    const opciones = cuerpo
      ? { method: "POST", headers: { "Content-Type": "application/json" }, body: JSON.stringify(cuerpo) }
      : undefined;
    const respuesta = await fetch("/api" + ruta, opciones);
    const datos = await respuesta.json();
    if (!respuesta.ok) {
      const detalle = Array.isArray(datos.detail)
        ? datos.detail.map((d) => d.msg.replace(/^Value error, /, "")).join(" ")
        : datos.detail;
      throw new Error(detalle || "Error al comunicarse con el servidor.");
    }
    return datos;
  }

  // Vuelve a la pantalla que se quería abrir si el rol puede verla; si no, a su inicio
  function entrar(usuario) {
    const sesion = Sesion.iniciar(usuario);
    const volver = new URLSearchParams(location.search).get("volver") || "";
    const pagina = volver.split("?")[0];
    const seguro = /^[a-z]+\.html(\?[\w=&%.-]*)?$/.test(volver) && pagina !== "login.html";
    location.replace(seguro && Sesion.puedeVer(pagina, sesion) ? volver : Sesion.inicioDe(sesion));
  }

  function mostrarPestana(registro) {
    $("form-entrar").hidden = registro;
    $("form-registro").hidden = !registro;
    const [activa, inactiva] = registro ? ["pestana-registro", "pestana-entrar"] : ["pestana-entrar", "pestana-registro"];
    $(activa).setAttribute("aria-current", "page");
    $(inactiva).removeAttribute("aria-current");
    $("aviso").hidden = true;
  }

  async function iniciarSesion(evento) {
    evento.preventDefault();
    const usuario = $("entrar-usuario").value.trim();
    const contrasena = $("entrar-contrasena").value;
    if (!usuario || !contrasena) {
      avisar("Escribe tu usuario y tu contraseña.", true);
      return;
    }
    try {
      entrar(await llamar("/sesion", { usuario, contrasena }));
    } catch (e) {
      avisar(e.message, true);
      $("entrar-contrasena").select();
    }
  }

  async function registrar(evento) {
    evento.preventDefault();
    const form = $("form-registro");
    const datos = {
      usuario: form.elements.usuario.value.trim(),
      nombre: form.elements.nombre.value.trim(),
      email: form.elements.email.value.trim(),
      rol: form.elements.rol.value,
      obra_id: form.elements.rol.value === Sesion.ROLES.RESIDENTE ? form.elements.obra_id.value || null : null,
      contrasena: form.elements.contrasena.value,
    };
    if (datos.contrasena !== form.elements.confirmar.value) {
      avisar("Las contraseñas no coinciden.", true);
      return;
    }
    if (datos.rol === Sesion.ROLES.RESIDENTE && !datos.obra_id) {
      avisar("Elige la obra asignada al residente.", true);
      return;
    }
    try {
      await llamar("/usuarios", datos);
      // La cuenta recién creada entra con su contraseña, igual que en un inicio de sesión normal
      entrar(await llamar("/sesion", { usuario: datos.usuario, contrasena: datos.contrasena }));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function cargarObras() {
    try {
      const obras = await llamar("/obras");
      $("reg-obra").append(...obras.map((obra) => {
        const opcion = document.createElement("option");
        opcion.value = obra.id;
        opcion.textContent = obra.nombre + " · " + obra.id;
        return opcion;
      }));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function pintarDemo() {
    $("usuarios-demo").replaceChildren(...DEMO.map(([usuario, nombre, rol]) => {
      const boton = document.createElement("button");
      boton.type = "button";
      boton.className = "secundario";
      const fuerte = document.createElement("strong");
      fuerte.textContent = usuario;
      const detalle = document.createElement("small");
      detalle.textContent = nombre + " · " + rol;
      boton.append(fuerte, detalle);
      boton.addEventListener("click", () => {
        $("entrar-usuario").value = usuario;
        $("entrar-contrasena").focus();
      });
      const li = document.createElement("li");
      li.append(boton);
      return li;
    }));
  }

  // Con sesión abierta no tiene caso volver a entrar
  if (Sesion.actual()) {
    location.replace(Sesion.inicioDe(Sesion.actual()));
    return;
  }

  $("pestana-entrar").addEventListener("click", (e) => { e.preventDefault(); mostrarPestana(false); });
  $("pestana-registro").addEventListener("click", (e) => { e.preventDefault(); mostrarPestana(true); });
  $("reg-rol").addEventListener("change", () => {
    $("campo-obra").hidden = $("reg-rol").value !== Sesion.ROLES.RESIDENTE;
  });
  $("form-entrar").addEventListener("submit", iniciarSesion);
  $("form-registro").addEventListener("submit", registrar);

  pintarDemo();
  cargarObras();
  mostrarPestana(location.hash === "#registro");
  // La guía de pruebas manda el usuario sugerido en el ancla (#RESIDENTE-PAU)
  const sugerido = decodeURIComponent(location.hash.slice(1));
  if (sugerido && sugerido !== "registro") {
    $("entrar-usuario").value = sugerido;
    $("entrar-contrasena").focus();
  }
  if (new URLSearchParams(location.search).get("volver")) {
    avisar("Inicia sesión para continuar.");
  }
})();
