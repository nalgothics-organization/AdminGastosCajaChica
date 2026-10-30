// Bandeja de autorización: aprobar o rechazar solicitudes de fondo (RF05/HU05).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, leer, guardar, etiquetaEstado, dinero } = window.Caja;
  const CLAVE_AUTORIZADOR = "cajaChica.autorizador";
  const $ = (id) => document.getElementById(id);

  function cargarIdentidad() {
    try {
      const guardado = JSON.parse(leer(CLAVE_AUTORIZADOR) || "{}");
      $("rol").value = guardado.rol || "Administración";
      $("nombre").value = guardado.nombre || "";
    } catch (e) {
      // Datos locales dañados: se piden de nuevo
    }
  }

  function identidad() {
    const nombre = $("nombre").value.trim();
    const rol = $("rol").value;
    guardar(CLAVE_AUTORIZADOR, JSON.stringify({ nombre, rol }));
    return {
      autorizador_id: rol.toUpperCase().slice(0, 3) + "-" + nombre.toUpperCase().replace(/\s+/g, "-"),
      autorizador_nombre: nombre,
      rol_autorizador: rol,
    };
  }

  async function decidir(solicitud, accion, monto, comentario) {
    if ($("nombre").value.trim().length < 3) {
      avisar("Escribe tu nombre para registrar quién decide.", true);
      return;
    }
    const cuerpo = { ...identidad(), comentario: comentario.trim() || null };
    if (accion === "aprobar") {
      cuerpo.monto_autorizado = monto || null;
    }
    try {
      await llamar("/solicitudes/" + solicitud.id + "/" + accion, enviarJson("POST", cuerpo));
      avisar(solicitud.folio + (accion === "aprobar" ? " aprobada." : " rechazada."));
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  // La foto subida desde la solicitud se muestra en línea; cualquier otro enlace se ofrece como vínculo
  function crearEvidencia(url) {
    if (url.startsWith("/api/evidencias/")) {
      return el("a", { href: url, target: "_blank", rel: "noopener" },
        el("img", { className: "evidencia-autorizacion", src: url, alt: "Evidencia de la necesidad", loading: "lazy" }));
    }
    if (/^https?:\/\//.test(url)) {
      return el("a", { className: "enlace-evidencia", href: url, target: "_blank", rel: "noopener noreferrer", texto: "Ver evidencia" });
    }
    return el("p", { className: "nota", texto: "Evidencia: " + url });
  }

  function crearTarjeta(solicitud) {
    const monto = el("input", { type: "number", min: "0.01", step: "0.01", value: solicitud.monto_solicitado });
    const comentario = el("input", { type: "text", placeholder: "Comentario (obligatorio al rechazar)" });
    const aprobar = el("button", { type: "button", texto: "Aprobar" });
    const rechazar = el("button", { type: "button", className: "rechazar", texto: "Rechazar" });
    aprobar.addEventListener("click", () => decidir(solicitud, "aprobar", monto.value, comentario.value));
    rechazar.addEventListener("click", () => decidir(solicitud, "rechazar", null, comentario.value));

    const sinPermiso = solicitud.nivel_autorizacion === "Dirección" && $("rol").value !== "Dirección";
    aprobar.disabled = sinPermiso;
    rechazar.disabled = sinPermiso;

    return el("div", { className: "tarjeta" },
      el("h3", { texto: solicitud.folio }),
      el("span", { className: "etiqueta", texto: "Autoriza: " + solicitud.nivel_autorizacion }),
      el("p", { texto: solicitud.concepto }),
      el("dl", {},
        el("dt", { texto: "Obra" }), el("dd", { texto: solicitud.obra_id }),
        el("dt", { texto: "Etapa · partida" }),
        el("dd", { texto: solicitud.etapa_construccion + " · " + solicitud.partida_categoria }),
        el("dt", { texto: "Residente" }), el("dd", { texto: solicitud.solicitante_id }),
        el("dt", { texto: "Urgencia" }), el("dd", { texto: solicitud.urgencia }),
        el("dt", { texto: "Costo estimado" }), el("dd", { texto: dinero(solicitud.costo_estimado) }),
        el("dt", { texto: "Solicitado" }), el("dd", { texto: dinero(solicitud.monto_solicitado) })
      ),
      crearEvidencia(solicitud.evidencia_url),
      sinPermiso ? el("p", { className: "nota", texto: "Excede el límite de Administración: solo Dirección decide." }) : null,
      el("label", { texto: "Monto a autorizar" }), monto,
      el("label", { texto: "Comentario" }), comentario,
      el("div", { className: "acciones" }, aprobar, rechazar)
    );
  }

  function crearDecidida(solicitud) {
    const decision = solicitud.autorizacion;
    const detalle = decision
      ? decision.autorizador_nombre + " (" + decision.rol_autorizador + ")"
        + (decision.comentario ? ": " + decision.comentario : "")
      : "";
    return el("li", {},
      el("div", { className: "tarjeta" },
        el("strong", { texto: solicitud.folio + " " }),
        etiquetaEstado(solicitud.estado),
        el("p", { className: "nota", texto: detalle })
      )
    );
  }

  async function cargar() {
    try {
      const todas = await llamar("/solicitudes");
      const pendientes = todas.filter((s) => s.estado === "Pendiente");
      const decididas = todas.filter((s) => s.autorizacion).slice(-5).reverse();
      $("pendientes").replaceChildren(...pendientes.map(crearTarjeta));
      $("vacio").hidden = pendientes.length > 0;
      $("decididas").replaceChildren(...decididas.map(crearDecidida));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("rol").addEventListener("change", cargar);
  cargarIdentidad();
  cargar();
})();
