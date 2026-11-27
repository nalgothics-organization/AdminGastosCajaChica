// Obras activas con sus partidas y su fondo de caja chica; alta y baja lógica de obras (RF02/HU02).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, dinero } = window.Caja;
  const $ = (id) => document.getElementById(id);

  function crearTarjeta(obra, fondo) {
    const baja = el("button", { type: "button", className: "rechazar", texto: "Dar de baja" });
    baja.addEventListener("click", () => darDeBaja(obra));
    return el("div", { className: "tarjeta" },
      el("h3", { texto: obra.nombre }),
      el("p", { className: "nota mono", texto: obra.id + " · " + obra.estado }),
      fondo
        ? el("dl", {},
          el("dt", { texto: "Fondo de caja chica" }), el("dd", { texto: dinero(fondo.presupuesto_caja_chica) }),
          el("dt", { texto: "Disponible" }), el("dd", { texto: dinero(fondo.disponible_caja_chica) }),
          el("dt", { texto: "Fondo de contingencia" }), el("dd", { texto: dinero(fondo.fondo_contingencia) }))
        : el("p", { className: "alerta ambar", texto: "Sin fondo de caja chica asignado." }),
      el("h4", { texto: "Partidas" }),
      el("ul", {}, obra.partidas.filter((p) => p.activo).map((p) =>
        el("li", { texto: p.clave + " · " + p.nombre + " · " + dinero(p.monto_presupuestado) }))),
      el("div", { className: "acciones inicio" }, baja)
    );
  }

  async function cargar() {
    try {
      const [obras, catalogo] = await Promise.all([llamar("/obras"), llamar("/catalogo/obras")]);
      const fondos = Object.fromEntries(catalogo.map((o) => [o.id, o]));
      $("obras").replaceChildren(...obras.map((o) => crearTarjeta(o, fondos[o.id])));
      $("vacio").hidden = obras.length > 0;
    } catch (e) {
      avisar(e.message, true);
    }
  }

  async function darDeBaja(obra) {
    if (!confirm("¿Dar de baja " + obra.id + "? Ya no se podrá elegir en solicitudes nuevas.")) {
      return;
    }
    try {
      await llamar("/obras/" + encodeURIComponent(obra.id), { method: "DELETE" });
      avisar(obra.id + " dada de baja.");
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function agregarPartida(clave, nombre, monto) {
    const quitar = el("button", { type: "button", className: "secundario", texto: "Quitar" });
    const renglon = el("tr", {},
      el("td", {}, el("input", { type: "text", name: "partida_clave", value: clave || "", placeholder: "P-01" })),
      el("td", {}, el("input", { type: "text", name: "partida_nombre", value: nombre || "", placeholder: "Materiales" })),
      el("td", {}, el("input", { type: "number", name: "partida_monto", min: "0", step: "0.01", value: monto || "" })),
      el("td", {}, quitar));
    quitar.addEventListener("click", () => renglon.remove());
    $("partidas").append(renglon);
  }

  async function registrar(evento) {
    evento.preventDefault();
    const form = $("form-obra");
    const partidas = [...$("partidas").querySelectorAll("tr")].map((tr) => ({
      clave: tr.querySelector('[name="partida_clave"]').value.trim(),
      nombre: tr.querySelector('[name="partida_nombre"]').value.trim(),
      monto_presupuestado: tr.querySelector('[name="partida_monto"]').value || "0",
    })).filter((p) => p.clave || p.nombre);
    try {
      const obra = await llamar("/obras", enviarJson("POST", {
        id: $("obra-id").value.trim(),
        nombre: $("obra-nombre").value.trim(),
        partidas,
      }));
      avisar(obra.id + " registrada con " + obra.partidas.length + " partida(s).");
      form.reset();
      $("partidas").replaceChildren();
      agregarPartida();
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("agregar-partida").addEventListener("click", () => agregarPartida());
  $("form-obra").addEventListener("submit", registrar);
  agregarPartida("P-01", "Materiales", "");
  cargar();
})();
