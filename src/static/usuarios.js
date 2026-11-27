// Alta, consulta y baja lógica de usuarios con rol (RF15/HU20).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el } = window.Caja;
  const $ = (id) => document.getElementById(id);
  const RESIDENTE = window.Sesion.ROLES.RESIDENTE;

  function fila(usuario) {
    const propio = usuario.usuario === window.Sesion.usuario();
    const baja = el("button", { type: "button", className: "rechazar", texto: "Dar de baja", disabled: propio });
    baja.title = propio ? "No puedes darte de baja a ti mismo" : "";
    baja.addEventListener("click", () => darDeBaja(usuario));
    return el("tr", {},
      el("td", { className: "mono fuerte", texto: usuario.usuario }),
      el("td", {}, el("strong", { texto: usuario.nombre }), el("br"), el("small", { className: "nota", texto: usuario.email })),
      el("td", {}, el("span", { className: "pastilla", texto: usuario.rol })),
      el("td", { className: "mono", texto: usuario.obra_id || "—" }),
      el("td", {}, baja));
  }

  async function cargar() {
    const rol = $("filtro-rol").value;
    try {
      const usuarios = await llamar("/usuarios" + (rol ? "?rol=" + encodeURIComponent(rol) : ""));
      $("filas").replaceChildren(...usuarios.map(fila));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function darDeBaja(usuario) {
    if (!confirm("¿Dar de baja a " + usuario.nombre + "? Ya no podrá iniciar sesión; sus registros se conservan.")) {
      return;
    }
    try {
      await llamar("/usuarios/" + usuario.id, { method: "DELETE" });
      avisar(usuario.usuario + " dado de baja.");
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function crear(evento) {
    evento.preventDefault();
    const form = $("form-usuario");
    const rol = form.elements.rol.value;
    try {
      const nuevo = await llamar("/usuarios", enviarJson("POST", {
        usuario: form.elements.usuario.value.trim(),
        nombre: form.elements.nombre.value.trim(),
        email: form.elements.email.value.trim(),
        rol,
        obra_id: rol === RESIDENTE ? form.elements.obra_id.value || null : null,
        contrasena: form.elements.contrasena.value,
      }));
      avisar(nuevo.usuario + " creado como " + nuevo.rol + ".");
      form.reset();
      $("campo-obra").hidden = false;
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function cargarObras() {
    try {
      const obras = await llamar("/obras");
      $("nuevo-obra").append(...obras.map((o) => el("option", { value: o.id, texto: o.nombre + " · " + o.id })));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("filtro-rol").addEventListener("change", cargar);
  $("nuevo-rol").addEventListener("change", () => {
    $("campo-obra").hidden = $("nuevo-rol").value !== RESIDENTE;
  });
  $("form-usuario").addEventListener("submit", crear);
  cargarObras();
  cargar();
})();
