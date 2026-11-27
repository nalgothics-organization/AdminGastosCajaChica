// Datos de la sesión, apartados del rol y cambio de contraseña (RF15/HU20).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el } = window.Caja;
  const Sesion = window.Sesion;
  const $ = (id) => document.getElementById(id);
  const sesion = Sesion.actual();
  if (!sesion) {
    return;
  }

  function pintar() {
    $("datos").replaceChildren(
      el("dt", { texto: "Usuario" }), el("dd", { className: "mono", texto: sesion.usuario }),
      el("dt", { texto: "Nombre" }), el("dd", { texto: sesion.nombre }),
      el("dt", { texto: "Correo" }), el("dd", { texto: sesion.email }),
      el("dt", { texto: "Rol" }), el("dd", { texto: sesion.rol }),
      el("dt", { texto: "Obra" }), el("dd", { className: "mono", texto: sesion.obra_id || "Todas" })
    );
    $("apartados").replaceChildren(...Sesion.PANTALLAS
      .filter(([, , roles]) => roles.includes(sesion.rol))
      .map(([ruta, texto]) => el("li", {}, el("a", { href: ruta, texto }))));
  }

  async function cambiar(evento) {
    evento.preventDefault();
    const form = $("form-contrasena");
    if (form.elements.nueva.value !== form.elements.confirmar.value) {
      avisar("La contraseña nueva y su confirmación no coinciden.", true);
      return;
    }
    try {
      await llamar("/usuarios/" + sesion.id + "/contrasena", enviarJson("PUT", {
        actual: form.elements.actual.value,
        nueva: form.elements.nueva.value,
      }));
      form.reset();
      avisar("Contraseña actualizada.");
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("form-contrasena").addEventListener("submit", cambiar);
  pintar();
})();
