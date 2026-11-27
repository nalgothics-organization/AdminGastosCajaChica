// Bandeja de autorización: aprobar o rechazar solicitudes de fondo (RF05/HU05)
// y mostrar el bloqueo por comprobaciones vencidas del residente (RF04/HU04).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, leer, guardar, etiquetaEstado, dinero, CLASIFICACIONES } = window.Caja;
  const CLAVE_AUTORIZADOR = "cajaChica.autorizador";
  const $ = (id) => document.getElementById(id);

  // Quién decide sale de la sesión iniciada; el servidor toma el nombre y el rol de su registro
  function cargarIdentidad() {
    const sesion = window.Sesion.actual();
    $("usuario").value = sesion ? sesion.usuario : leer(CLAVE_AUTORIZADOR);
    $("usuario-nombre").textContent = sesion ? sesion.nombre + " (" + sesion.usuario + ")" : "";
    $("usuario-rol").textContent = sesion ? sesion.rol : "";
  }

  function identidad() {
    const usuario = $("usuario").value.trim().toUpperCase();
    guardar(CLAVE_AUTORIZADOR, usuario);
    return { autorizador_id: usuario };
  }

  async function decidir(solicitud, accion, monto, comentario, clasificacion) {
    if (!$("usuario").value.trim()) {
      avisar("Escribe tu usuario para registrar quién decide.", true);
      return;
    }
    // RF14/HU15: al aprobar se decide si el gasto se cobra al cliente o sale del fondo de contingencia
    if (accion === "aprobar" && !clasificacion) {
      avisar("Elige si el gasto es cobrable al cliente o sale del fondo de contingencia.", true);
      return;
    }
    const cuerpo = { ...identidad(), comentario: comentario.trim() || null };
    if (accion === "aprobar") {
      cuerpo.monto_autorizado = monto || null;
      cuerpo.clasificacion = clasificacion;
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

  function crearBloqueo(bloqueo) {
    const cantidad = bloqueo.comprobaciones_vencidas;
    return el("div", { className: "alerta rojo", role: "note" },
      el("span", { className: "etiqueta rechazado", texto: "Bloqueada" }),
      el("p", {}, el("strong", {
        texto: cantidad + (cantidad === 1 ? " comprobación pendiente" : " comprobaciones pendientes")
          + " con más de " + bloqueo.limite_dias + " días · " + dinero(bloqueo.monto_por_comprobar),
      })),
      el("p", { className: "nota", texto: "Folios por comprobar: " + bloqueo.folios_vencidos.join(", ") })
    );
  }

  // Sin opción preseleccionada: quien aprueba tiene que elegir una a conciencia
  function crearClasificacion(solicitudId) {
    return el("fieldset", {},
      el("legend", { texto: "¿Quién paga el gasto?" }),
      Object.entries(CLASIFICACIONES).map(([valor, texto]) =>
        el("label", {}, el("input", { type: "radio", name: "clasificacion-" + solicitudId, value: valor }), " " + texto))
    );
  }

  function crearTarjeta(solicitud) {
    const monto = el("input", { type: "number", min: "0.01", step: "0.01", value: solicitud.monto_solicitado });
    const comentario = el("input", { type: "text", placeholder: "Comentario (obligatorio al rechazar)" });
    const aprobar = el("button", { type: "button", texto: "Aprobar" });
    const rechazar = el("button", { type: "button", className: "rechazar", texto: "Rechazar" });
    const clasificacion = crearClasificacion(solicitud.id);
    const elegida = () => {
      const opcion = clasificacion.querySelector("input:checked");
      return opcion ? opcion.value : null;
    };
    aprobar.addEventListener("click", () => decidir(solicitud, "aprobar", monto.value, comentario.value, elegida()));
    rechazar.addEventListener("click", () => decidir(solicitud, "rechazar", null, comentario.value));

    // Con comprobaciones vencidas no se aprueba; rechazar sigue disponible para cerrar la solicitud
    const bloqueo = solicitud.bloqueo && solicitud.bloqueo.bloqueada ? solicitud.bloqueo : null;
    const soloDireccion = solicitud.nivel_autorizacion === "Dirección";
    // Administración no decide lo que excede su límite; el servidor también lo rechaza con 403
    const sesion = window.Sesion.actual();
    const sinPermiso = soloDireccion && (!sesion || sesion.rol !== "Dirección");
    aprobar.disabled = sinPermiso || Boolean(bloqueo);
    rechazar.disabled = sinPermiso;

    return el("div", { className: "tarjeta" + (bloqueo ? " bloqueada" : "") },
      el("h3", { texto: solicitud.folio }),
      el("span", { className: "etiqueta", texto: "Autoriza: " + solicitud.nivel_autorizacion }),
      bloqueo ? crearBloqueo(bloqueo) : null,
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
      soloDireccion ? el("p", { className: "nota", texto: "Excede el límite de Administración: solo Dirección decide." }) : null,
      clasificacion,
      el("label", { texto: "Monto a autorizar" }), monto,
      el("label", { texto: "Comentario" }), comentario,
      el("div", { className: "acciones" }, aprobar, rechazar)
    );
  }

  function crearDecidida(solicitud) {
    const decision = solicitud.autorizacion;
    const detalle = decision
      ? decision.autorizador_nombre + " (" + decision.rol_autorizador + ")"
        + (decision.clasificacion ? " · " + CLASIFICACIONES[decision.clasificacion] : "")
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
      const bloqueadas = pendientes.filter((s) => s.bloqueo && s.bloqueo.bloqueada).length;
      const decididas = todas.filter((s) => s.autorizacion).slice(-5).reverse();
      $("pendientes").replaceChildren(...pendientes.map(crearTarjeta));
      $("vacio").hidden = pendientes.length > 0;
      $("contador-bloqueadas").textContent = bloqueadas
        ? bloqueadas + (bloqueadas === 1 ? " bloqueada" : " bloqueadas") + " por comprobaciones vencidas"
        : "";
      $("contador-bloqueadas").hidden = bloqueadas === 0;
      $("decididas").replaceChildren(...decididas.map(crearDecidida));
    } catch (e) {
      avisar(e.message, true);
    }
  }

  cargarIdentidad();
  cargar();
})();
