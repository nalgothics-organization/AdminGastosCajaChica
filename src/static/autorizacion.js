// Bandeja de autorización: aprobar o rechazar solicitudes de fondo (RF05/HU05),
// mostrar el bloqueo por comprobaciones vencidas del residente (RF04/HU04)
// y registrar la entrega del recurso aprobado desde la misma pantalla (RF06/HU06).
(function () {
  "use strict";

  const { llamar, enviarJson, avisar, el, leer, guardar, etiquetaEstado, dinero } = window.Caja;
  const CLAVE_AUTORIZADOR = "cajaChica.autorizador";
  const FORMAS_ENTREGA = ["Efectivo", "Transferencia", "Tarjeta"];
  // Espejo de LONGITUD_MINIMA_REFERENCIA (src/models/solicitud.py); el backend valida de todos modos
  const LONGITUD_MINIMA_REFERENCIA = 3;
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

  function crearTarjeta(solicitud) {
    const monto = el("input", { type: "number", min: "0.01", step: "0.01", value: solicitud.monto_solicitado });
    const comentario = el("input", { type: "text", placeholder: "Comentario (obligatorio al rechazar)" });
    const aprobar = el("button", { type: "button", texto: "Aprobar" });
    const rechazar = el("button", { type: "button", className: "rechazar", texto: "Rechazar" });
    aprobar.addEventListener("click", () => decidir(solicitud, "aprobar", monto.value, comentario.value));
    rechazar.addEventListener("click", () => decidir(solicitud, "rechazar", null, comentario.value));

    const sinPermiso = solicitud.nivel_autorizacion === "Dirección" && $("rol").value !== "Dirección";
    // Con comprobaciones vencidas no se aprueba; rechazar sigue disponible para cerrar la solicitud
    const bloqueo = solicitud.bloqueo && solicitud.bloqueo.bloqueada ? solicitud.bloqueo : null;
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

  // Fecha local en formato AAAA-MM-DD; toISOString() daría la de UTC, que de noche ya es la de mañana
  function hoyLocal() {
    const ahora = new Date();
    const mes = String(ahora.getMonth() + 1).padStart(2, "0");
    const dia = String(ahora.getDate()).padStart(2, "0");
    return ahora.getFullYear() + "-" + mes + "-" + dia;
  }

  const fechaLegible = (iso) => iso.split("-").reverse().join("/");

  async function registrarEntrega(solicitud, forma, referencia, fecha) {
    if ($("nombre").value.trim().length < 3) {
      avisar("Escribe tu nombre para registrar quién entrega el recurso.", true);
      return;
    }
    if (forma !== "Efectivo" && referencia.trim().length < LONGITUD_MINIMA_REFERENCIA) {
      avisar("Indica la referencia bancaria de la " + forma.toLowerCase() + ".", true);
      return;
    }
    const quien = identidad();
    const cuerpo = {
      entregado_por_id: quien.autorizador_id,
      entregado_por_nombre: quien.autorizador_nombre,
      rol_entrega: quien.rol_autorizador,
      forma_entrega: forma,
      fecha_entrega: fecha || null,
      referencia: referencia.trim() || null,
    };
    try {
      await llamar("/solicitudes/" + solicitud.id + "/entrega", enviarJson("POST", cuerpo));
      avisar("Entrega de " + solicitud.folio + " registrada.");
      cargar();
    } catch (e) {
      avisar(e.message, true);
    }
  }

  function crearTarjetaEntrega(solicitud) {
    const decision = solicitud.autorizacion;
    const monto = decision && decision.monto_autorizado ? decision.monto_autorizado : solicitud.monto_solicitado;
    const forma = el("select", {}, FORMAS_ENTREGA.map((f) => el("option", { value: f, texto: f })));
    const rotuloReferencia = el("label", { texto: "Referencia bancaria" });
    const referencia = el("input", { type: "text", maxLength: 120, autocomplete: "off" });
    const fecha = el("input", { type: "date", value: hoyLocal(), max: hoyLocal() });
    const entregar = el("button", { type: "button", texto: "Registrar entrega" });

    // En efectivo no hay referencia bancaria: basta con marcarlo; el folio del recibo es opcional
    function ajustarReferencia() {
      const efectivo = forma.value === "Efectivo";
      rotuloReferencia.textContent = efectivo ? "Folio del recibo (opcional)" : "Referencia bancaria";
      referencia.placeholder = efectivo ? "Entregado en efectivo" : "Ej. SPEI-20261127-0381";
    }
    forma.addEventListener("change", ajustarReferencia);
    ajustarReferencia();
    entregar.addEventListener("click", () => registrarEntrega(solicitud, forma.value, referencia.value, fecha.value));

    return el("div", { className: "tarjeta" },
      el("h3", { texto: solicitud.folio }),
      el("span", { className: "etiqueta aprobado", texto: "Aprobada" }),
      el("p", { texto: solicitud.concepto }),
      el("dl", {},
        el("dt", { texto: "Obra" }), el("dd", { texto: solicitud.obra_id }),
        el("dt", { texto: "Residente" }), el("dd", { texto: solicitud.solicitante_id }),
        el("dt", { texto: "Autorizó" }),
        el("dd", { texto: decision ? decision.autorizador_nombre + " (" + decision.rol_autorizador + ")" : "—" }),
        el("dt", { texto: "Monto a entregar" }), el("dd", { texto: dinero(monto) })
      ),
      el("label", { texto: "Forma de entrega" }), forma,
      rotuloReferencia, referencia,
      el("label", { texto: "Fecha de entrega" }), fecha,
      el("div", { className: "acciones" }, entregar)
    );
  }

  function crearEntregada(solicitud) {
    const entrega = solicitud.entrega;
    const detalle = [
      entrega.forma_entrega,
      entrega.referencia ? "ref. " + entrega.referencia : null,
      fechaLegible(entrega.fecha_entrega),
    ].filter(Boolean).join(" · ")
      + " — entregó " + entrega.entregado_por_nombre + " (" + entrega.rol_entrega + ")";
    return el("li", {},
      el("div", { className: "tarjeta" },
        el("strong", { texto: solicitud.folio + " " }),
        el("span", { className: "etiqueta entregado", texto: "Entregado" }),
        el("p", { className: "nota", texto: detalle })
      )
    );
  }

  // Las aprobadas sin entrega esperan aquí; las ya entregadas pasan al historial reciente
  function dibujarEntregas(todas) {
    const porEntregar = todas.filter((s) => s.estado === "Aprobado" && !s.entrega);
    const entregadas = todas
      .filter((s) => s.entrega)
      .sort((a, b) => new Date(b.entrega.fecha_registro) - new Date(a.entrega.fecha_registro))
      .slice(0, 5);
    $("por-entregar").replaceChildren(...porEntregar.map(crearTarjetaEntrega));
    $("vacio-entregas").hidden = porEntregar.length > 0;
    $("contador-entregas").textContent = porEntregar.length;
    $("contador-entregas").hidden = porEntregar.length === 0;
    $("entregadas").replaceChildren(...entregadas.map(crearEntregada));
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
      dibujarEntregas(todas);
    } catch (e) {
      avisar(e.message, true);
    }
  }

  $("rol").addEventListener("change", cargar);
  cargarIdentidad();
  cargar();
})();
