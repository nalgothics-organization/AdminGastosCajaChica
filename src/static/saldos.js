// Tablero de saldos por obra en tiempo real (RF10/HU10) con el fondo de contingencia (RF14/HU15).
(function () {
  "use strict";

  const { llamar, avisar, el, dinero } = window.Caja;
  const INTERVALO_MS = 10000;
  const $ = (id) => document.getElementById(id);

  function crearTarjeta(saldo) {
    // La barra muestra cuánto del fondo de caja chica ya está autorizado
    const porcentaje = Number(saldo.porcentaje_autorizado);
    const claseBarra = porcentaje > 100 ? "excedido" : porcentaje >= 80 ? "alerta" : "";
    const disponible = Number(saldo.disponible_caja_chica);
    const porComprobar = Number(saldo.por_comprobar);
    const sinSolicitud = Number(saldo.gasto_sin_solicitud);
    const contingencia = Number(saldo.disponible_contingencia);

    return el("div", { className: "tarjeta" },
      el("h3", { texto: saldo.nombre }),
      el("p", { className: "nota", texto: saldo.obra_id }),
      el("p", { className: "cifra" + (disponible < 0 ? " negativo" : ""), texto: dinero(saldo.disponible_caja_chica) }),
      el("p", { className: "nota", texto: "disponible de " + dinero(saldo.presupuesto_caja_chica) + " de caja chica" }),
      el("div", { className: "barra " + claseBarra },
        el("span", { style: "width:" + Math.min(porcentaje, 100) + "%" })),
      el("p", { className: "nota", texto: porcentaje + "% del fondo ya está autorizado" }),
      el("dl", {},
        el("dt", { texto: "Fondo de caja chica" }), el("dd", { texto: dinero(saldo.presupuesto_caja_chica) }),
        el("dt", { texto: "Autorizado" }), el("dd", { texto: dinero(saldo.autorizado) }),
        el("dt", { texto: "Comprobado" }), el("dd", { texto: dinero(saldo.comprobado) }),
        el("dt", { texto: "Por comprobar" }),
        el("dd", { className: porComprobar < 0 ? "negativo" : "", texto: dinero(saldo.por_comprobar) }),
        el("dt", { texto: "Pendiente de autorizar" }),
        el("dd", { texto: dinero(saldo.pendiente_autorizacion) + " (" + saldo.solicitudes_pendientes + ")" }),
        el("dt", { texto: "Pagado sin solicitud (por reponer)" }),
        el("dd", { className: sinSolicitud > 0 ? "negativo" : "", texto: dinero(saldo.gasto_sin_solicitud) }),
        el("dt", { texto: "En revisión de contabilidad" }), el("dd", { texto: String(saldo.comprobantes_en_revision) })
      ),
      el("h4", { texto: "Cobro al cliente y contingencia" }),
      el("dl", {},
        el("dt", { texto: "Por facturar al cliente" }), el("dd", { texto: dinero(saldo.gasto_cobrable_cliente) }),
        el("dt", { texto: "Fondo de contingencia" }), el("dd", { texto: dinero(saldo.fondo_contingencia) }),
        el("dt", { texto: "Cargado a contingencia" }), el("dd", { texto: dinero(saldo.gasto_contingencia) }),
        el("dt", { texto: "Contingencia disponible" }),
        el("dd", { className: contingencia < 0 ? "negativo" : "", texto: dinero(saldo.disponible_contingencia) })
      )
    );
  }

  async function cargar() {
    try {
      const saldos = await llamar("/saldos");
      $("obras").replaceChildren(...saldos.map(crearTarjeta));
      $("vacio").hidden = saldos.length > 0;
      $("actualizado").textContent = "Última lectura: " + new Date().toLocaleTimeString("es-MX");
    } catch (e) {
      avisar(e.message, true);
    }
  }

  cargar();
  setInterval(cargar, INTERVALO_MS);
})();
