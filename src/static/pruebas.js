// Guía de pruebas manuales: cada historia con el usuario que la prueba, los pasos y lo esperado.
// El avance se guarda en localStorage de este navegador; no se envía al servidor.
(function () {
  "use strict";

  const { el, leer, guardar, avisar } = window.Caja;
  const Sesion = window.Sesion;
  const $ = (id) => document.getElementById(id);
  const CLAVE_AVANCE = "cajaChica.pruebas";
  const R = "Residente de obra";
  const A = "Administración";
  const D = "Dirección";
  const C = "Contabilidad";

  // [id, historia, título, roles, usuarios sugeridos, pantalla, pasos: [acción, resultado esperado]]
  const SECCIONES = [
    {
      id: "preparacion", hu: "Inicio", titulo: "Preparar el entorno", roles: [R, A, D, C], usuarios: [], pantalla: null,
      pasos: [
        ["Copia .env.example a .env y define CONTRASENA_DEMO con una contraseña de prueba (mínimo 8 caracteres).",
          "El archivo .env existe y no se sube a Git."],
        ["Levanta la base con docker compose up -d db y carga los datos con python -m src.seed --reset.",
          "Imprime que creó 6 usuarios y 5 solicitudes con 4 comprobantes en 2 obras."],
        ["Arranca la API con python -m uvicorn src.main:app --reload y abre http://127.0.0.1:8000/app/.",
          "Sin sesión, cualquier pantalla te manda a Iniciar sesión."],
        ["Para probar el bloqueo (HU04) sin esperar 7 días, pon LIMITE_DIAS_COMPROBACION=0 en .env y reinicia la API.",
          "Cualquier fondo aprobado y sin comprobar cuenta como vencido."],
      ],
    },
    {
      id: "hu20", hu: "RF15 · HU20", titulo: "Usuarios, roles e inicio de sesión", roles: [R, A, D, C],
      usuarios: ["ADMIN-LAURA"], pantalla: ["login.html", "Iniciar sesión"],
      pasos: [
        ["Entra con un usuario existente y una contraseña incorrecta.",
          "Aparece \"Usuario o contraseña incorrectos.\" sin decir cuál de los dos falló."],
        ["En \"Crear cuenta\" registra un Residente de obra sin elegir obra.",
          "Pide elegir la obra asignada."],
        ["Registra un residente con obra y contraseña de 8+ caracteres.",
          "Entra directo a Mi caja chica con tu nombre y rol en la barra superior."],
        ["Intenta registrar otra cuenta con el mismo usuario o el mismo correo.",
          "Responde que el usuario o el correo ya existe."],
        ["Entra con cada rol de demostración y revisa las pestañas.",
          "Residente: Mi caja chica y Nueva solicitud. Administración/Dirección: Autorizaciones, Comprobantes, Obras y Usuarios. Contabilidad: Comprobantes. Todos: Saldos, Mi cuenta y esta guía."],
        ["Como residente, escribe autorizacion.html en la barra de direcciones.",
          "Muestra \"Esta pantalla no es para tu rol\" con un enlace a tu inicio."],
        ["En Mi cuenta cambia la contraseña poniendo mal la actual; luego hazlo bien, cierra sesión y entra con la nueva.",
          "La primera vez rechaza la contraseña actual; después entras con la nueva."],
        ["Como ADMIN-LAURA, en Usuarios crea un usuario de Contabilidad y luego dalo de baja.",
          "Desaparece de la lista y ya no puede iniciar sesión; sus registros se conservan."],
        ["Intenta dar de baja tu propio usuario.",
          "El botón está deshabilitado."],
      ],
    },
    {
      id: "hu01", hu: "RF01 · HU01 · HU02", titulo: "Solicitud de fondo", roles: [R],
      usuarios: ["RESIDENTE-PAU"], pantalla: ["solicitud.html", "Nueva solicitud"],
      pasos: [
        ["Abre Nueva solicitud.",
          "Tu obra asignada ya está elegida y muestra la caja chica disponible."],
        ["Envía la solicitud sin evidencia.",
          "Pide la evidencia de la necesidad."],
        ["Pega como evidencia un texto que no sea foto ni http(s), por ejemplo javascript:alert(1).",
          "Rechaza la evidencia."],
        ["Toma o sube una foto como evidencia y envía una solicitud de $1,200.",
          "Muestra la vista previa; la solicitud queda Pendiente y la autoriza Administración."],
        ["Escribe un monto de $7,500.",
          "Aparece el campo de firma digital de Dirección; sin firma no se envía."],
        ["Envía la de $7,500 con firma.",
          "Queda Pendiente y la autoriza Dirección."],
        ["En Mis solicitudes usa \"Retirar solicitud\" en una pendiente.",
          "Desaparece de tu lista y de la bandeja de autorización (borrado lógico)."],
      ],
    },
    {
      id: "hu05", hu: "RF05 · HU05", titulo: "Autorización de solicitudes", roles: [A, D],
      usuarios: ["ADMIN-LAURA", "DIR-CARLOS"], pantalla: ["autorizacion.html", "Autorizaciones"],
      pasos: [
        ["Entra como ADMIN-LAURA y abre Autorizaciones.",
          "Arriba dice que decides como Laura Méndez (Administración)."],
        ["Busca una solicitud de más de $5,000.",
          "Aprobar y Rechazar están deshabilitados y avisa que solo Dirección decide."],
        ["Aprueba una de hasta $5,000 sin elegir quién paga el gasto.",
          "Pide elegir si es cobrable al cliente o fondo de contingencia."],
        ["Aprueba con un monto mayor al solicitado.",
          "Rechaza el monto."],
        ["Aprueba con un monto menor y \"Cobrable al cliente\".",
          "Pasa a Decididas recientemente con tu nombre, rol y clasificación."],
        ["Rechaza otra sin comentario y luego con comentario.",
          "Sin comentario la rechaza el servidor; con comentario queda Rechazada."],
        ["Entra como DIR-CARLOS y aprueba la de más de $5,000.",
          "Dirección puede decidir cualquier monto."],
        ["Entra como el residente y revisa Mis solicitudes.",
          "Ve el estado, el monto autorizado, con qué se paga y el comentario."],
      ],
    },
    {
      id: "hu04", hu: "RF04 · HU04", titulo: "Bloqueo por comprobaciones vencidas", roles: [R, A],
      usuarios: ["RESIDENTE-PAU", "ADMIN-LAURA"], pantalla: ["autorizacion.html", "Autorizaciones"],
      pasos: [
        ["Con LIMITE_DIAS_COMPROBACION=0, entra como un residente que tenga un fondo aprobado sin comprobar completo y envía una solicitud nueva.",
          "Al enviar avisa que no se autorizará y en Mis solicitudes aparece el motivo en rojo."],
        ["Como ADMIN-LAURA abre Autorizaciones.",
          "La tarjeta sale marcada Bloqueada con el número de comprobaciones, el monto y los folios; el contador de bloqueadas aparece arriba."],
        ["Intenta aprobarla.",
          "Aprobar está deshabilitado (la API responde 423 si se intenta)."],
        ["Recházala con comentario.",
          "Rechazar sigue permitido."],
        ["Comprueba el total del fondo vencido y vuelve a la bandeja.",
          "Las solicitudes nuevas del residente ya no aparecen bloqueadas."],
      ],
    },
    {
      id: "hu16", hu: "RNF01 · HU16 · RNF05 · HU21", titulo: "Captura rápida y legibilidad de la foto", roles: [R],
      usuarios: ["RESIDENTE-PAU"], pantalla: ["index.html", "Mi caja chica"],
      pasos: [
        ["Abre Mi caja chica.",
          "La solicitud aprobada más reciente ya está elegida y el botón \"Escanear comprobante\" está fijo abajo."],
        ["Escanea o sube la foto de un comprobante.",
          "Avisa al instante que se sube en segundo plano y luego muestra los segundos desde que tocaste Escanear."],
        ["Sube una foto casi negra.",
          "Antes de enviarla pide repetirla; puedes usarla de todos modos o cancelar."],
        ["Con VALIDAR_LEGIBILIDAD=true, sube una foto borrosa o sin ningún monto.",
          "El servidor la rechaza y ofrece \"Repetir foto\" sin guardar nada."],
        ["Sube un archivo que no sea imagen o una imagen muy pequeña.",
          "Se rechaza con el motivo."],
        ["Abre la pantalla en el celular (o reduce la ventana a menos de 640 px).",
          "Solo se ven quién captura, la lista de solicitudes y los botones de escaneo; \"Salir\" cierra la sesión."],
      ],
    },
    {
      id: "hu11", hu: "RF11 · HU11", titulo: "Lectura de datos con OCR", roles: [R],
      usuarios: ["RESIDENTE-PAU"], pantalla: ["index.html", "Mi caja chica"],
      pasos: [
        ["Con VALIDAR_LEGIBILIDAD=true, escanea un ticket o factura real y toca \"Ver foto y datos\".",
          "Muestra la foto, el proveedor, la fecha, el monto y el tipo leídos; lo que no se leyó queda \"Por completar\"."],
        ["Despliega \"Texto leído de la foto\".",
          "Muestra los renglones que reconoció el OCR."],
        ["Toca \"Completar datos\".",
          "El formulario llega precargado con lo leído y resalta lo que falta; el concepto siempre lo escribes tú."],
      ],
    },
    {
      id: "hu07", hu: "RF07 · HU07", titulo: "Completar y cerrar la comprobación", roles: [R],
      usuarios: ["RESIDENTE-PAU"], pantalla: ["index.html", "Mi caja chica"],
      pasos: [
        ["Abre un borrador de una solicitud de Materiales y guarda con fecha futura.",
          "Rechaza la fecha futura."],
        ["Completa los datos como Factura y usa \"Guardar y cerrar\".",
          "Queda Comprobado y suma a lo comprobado de la solicitud y de la obra."],
        ["Haz lo mismo con un Ticket o una Nota simple.",
          "Pasa a Revisión contabilidad."],
        ["Comprueba un gasto de una solicitud de Renta de Maquinaria o Mano de Obra sin horas.",
          "Aparecen los campos de horas y no se cierra sin ellas."],
        ["Captura una foto y usa \"Descartar\".",
          "El borrador desaparece (borrado lógico); un comprobante cerrado ya no se puede descartar."],
      ],
    },
    {
      id: "hu08", hu: "RF08 · HU08", titulo: "Exigencia de comprobante y cierre automático", roles: [R],
      usuarios: ["RESIDENTE-PAU"], pantalla: ["index.html", "Mi caja chica"],
      pasos: [
        ["Con VALIDAR_LEGIBILIDAD=true y CIERRE_AUTOMATICO=true, escanea una factura nítida contra una solicitud aprobada de Materiales.",
          "Si se leyeron los 4 datos con confianza alta, el envío dice \"y comprobado\" sin más pasos."],
        ["Haz lo mismo con un ticket nítido.",
          "Queda \"en revisión de contabilidad\" sin más pasos."],
        ["Pon CIERRE_AUTOMATICO=false, reinicia y repite.",
          "Siempre queda en Borrador para que el residente lo confirme."],
      ],
    },
    {
      id: "propio", hu: "RF02", titulo: "Gasto pagado sin solicitud", roles: [R],
      usuarios: ["RESIDENTE-LUIS"], pantalla: ["index.html", "Mi caja chica"],
      pasos: [
        ["Elige \"Gasto pagado por mi cuenta\" y escanea la foto.",
          "Se registra sin solicitud."],
        ["Complétalo sin obra, etapa, partida o sin decir quién paga.",
          "Pide esos datos."],
        ["Complétalo con todo y ciérralo, aunque sea factura.",
          "Pasa a Revisión contabilidad y en Saldos suma a \"Pagado sin solicitud (por reponer)\"."],
      ],
    },
    {
      id: "hu15", hu: "RF14 · HU15", titulo: "Cobrable al cliente y fondo de contingencia", roles: [A, R],
      usuarios: ["ADMIN-LAURA", "RESIDENTE-PAU"], pantalla: ["saldos.html", "Saldos por obra"],
      pasos: [
        ["Aprueba una solicitud como \"Fondo de contingencia\" y otra como \"Cobrable al cliente\".",
          "Cada una muestra con qué se paga en Decididas y en Mis solicitudes."],
        ["Como residente, comprueba y cierra un gasto de cada una.",
          "Los comprobantes heredan la clasificación de su solicitud."],
        ["Abre Saldos por obra.",
          "\"Por facturar al cliente\" y \"Cargado a contingencia\" suben; \"Contingencia disponible\" baja."],
      ],
    },
    {
      id: "hu10", hu: "RF10 · HU10", titulo: "Saldos por obra en tiempo real", roles: [R, A, D, C],
      usuarios: ["DIR-CARLOS"], pantalla: ["saldos.html", "Saldos por obra"],
      pasos: [
        ["Abre Saldos por obra en una ventana y aprueba una solicitud en otra.",
          "En máximo 10 segundos baja el disponible y sube lo autorizado, sin recargar."],
        ["Revisa la barra de cada obra.",
          "Cambia de color al pasar del 80% autorizado y se marca excedida arriba del 100%."],
        ["Revisa los contadores.",
          "Pendiente de autorizar, comprobantes en revisión y pagado sin solicitud cuadran con las otras pantallas."],
      ],
    },
    {
      id: "correcciones", hu: "AGENTS.md §8", titulo: "Ajustes y reversos (nada se borra ni se edita)", roles: [C, A, D],
      usuarios: ["CONT-SOFIA"], pantalla: ["revision.html", "Comprobantes"],
      pasos: [
        ["Como CONT-SOFIA abre Comprobantes.",
          "Muestra lo que está en Revisión contabilidad con los totales arriba."],
        ["Abre un comprobante en Borrador.",
          "No ofrece corrección: el borrador lo completa el residente."],
        ["Abre uno cerrado y registra un Ajuste con otro monto y un motivo.",
          "Se crea un registro Ajuste en revisión que referencia al original; el original no cambia."],
        ["Revisa Saldos por obra.",
          "Lo comprobado usa el monto del ajuste, no el del original."],
        ["Registra un Reverso del mismo original.",
          "Pide confirmación; su monto deja de contar en los saldos."],
        ["Intenta otra corrección sobre ese original o sobre el ajuste.",
          "Ya no se permite: el original está reversado y las correcciones solo van sobre originales."],
      ],
    },
    {
      id: "obras", hu: "RF02 · HU02", titulo: "Obras y partidas presupuestales", roles: [A, D],
      usuarios: ["ADMIN-LAURA"], pantalla: ["obras.html", "Obras"],
      pasos: [
        ["Abre Obras.",
          "Cada obra muestra sus partidas y su fondo de caja chica y de contingencia."],
        ["Registra una obra con una partida llamada \"Varios\" u \"Otros\".",
          "Se rechaza: no se permiten partidas genéricas."],
        ["Registra una obra con un identificador que ya existe.",
          "Se rechaza por duplicada."],
        ["Registra una obra válida con dos partidas.",
          "Aparece en la lista, sin fondo de caja chica asignado."],
        ["Da de baja una obra y luego, como residente, envía una solicitud a esa obra.",
          "La solicitud se rechaza porque la obra no está activa. Reinicia la API para restaurar las obras de ejemplo."],
      ],
    },
    {
      id: "api", hu: "API", titulo: "Documentación interactiva", roles: [A, D], usuarios: [], pantalla: null,
      pasos: [
        ["Abre http://127.0.0.1:8000/docs.",
          "Están las secciones Solicitudes, Comprobantes, Saldos, Obras y Usuarios."],
        ["Prueba POST /api/sesion con una contraseña incorrecta.",
          "Responde 401."],
        ["Prueba GET /api/usuarios.",
          "Ningún usuario incluye la contraseña."],
      ],
    },
  ];

  let avance = {};
  try {
    avance = JSON.parse(leer(CLAVE_AVANCE) || "{}");
  } catch (e) {
    avance = {};
  }

  const clave = (seccion, indice) => seccion.id + ":" + indice;

  function visibles() {
    const rol = $("filtro-rol").value;
    return SECCIONES.filter((s) => !rol || s.roles.includes(rol));
  }

  function pintarAvance() {
    const total = SECCIONES.reduce((t, s) => t + s.pasos.length, 0);
    const hechos = SECCIONES.reduce((t, s) => t + s.pasos.filter((_, i) => avance[clave(s, i)]).length, 0);
    const porcentaje = total ? Math.round((hechos * 100) / total) : 0;
    $("avance-cifra").textContent = porcentaje + "%";
    $("avance-barra").style.width = porcentaje + "%";
    $("avance-detalle").textContent = hechos + " de " + total + " pasos verificados";
  }

  // Enlace para cambiar al usuario sugerido: cierra la sesión y deja el usuario escrito en el login
  function chipUsuario(usuario) {
    const propio = Sesion.usuario() === usuario;
    const boton = el("button", {
      type: "button",
      className: "pastilla " + (propio ? "verde" : "azul") + " chip",
      texto: propio ? usuario + " · tú" : "Entrar como " + usuario,
      disabled: propio,
    });
    boton.addEventListener("click", () => {
      Sesion.cerrar();
      location.href = "login.html?volver=pruebas.html#" + encodeURIComponent(usuario);
    });
    return boton;
  }

  function pintarSeccion(seccion) {
    const soloPendientes = $("solo-pendientes").value === "1";
    const hechos = seccion.pasos.filter((_, i) => avance[clave(seccion, i)]).length;
    const pasos = seccion.pasos
      .map((paso, i) => [paso, i])
      .filter(([, i]) => !soloPendientes || !avance[clave(seccion, i)]);
    const puedeAbrir = seccion.pantalla && Sesion.puedeVer(seccion.pantalla[0], Sesion.actual());
    return el("section", { className: "panel prueba", id: "prueba-" + seccion.id },
      el("div", { className: "prueba-encabezado" },
        el("div", {},
          el("span", { className: "insignia-clara", texto: seccion.hu }),
          el("h2", { texto: seccion.titulo })),
        el("span", { className: "pastilla " + (hechos === seccion.pasos.length ? "verde" : "ambar"),
          texto: hechos + "/" + seccion.pasos.length })),
      el("div", { className: "prueba-meta" },
        el("small", { texto: "Roles: " + seccion.roles.join(", ") }),
        ...seccion.usuarios.map(chipUsuario),
        puedeAbrir ? el("a", { className: "ver-comprobante", href: seccion.pantalla[0], texto: "Abrir " + seccion.pantalla[1] + " →" }) : null),
      pasos.length
        ? el("ol", { className: "pasos-prueba" }, pasos.map(([[accion, esperado], i]) => {
          const id = "paso-" + seccion.id + "-" + i;
          const casilla = el("input", { type: "checkbox", id, checked: Boolean(avance[clave(seccion, i)]) });
          casilla.addEventListener("change", () => {
            if (casilla.checked) {
              avance[clave(seccion, i)] = true;
            } else {
              delete avance[clave(seccion, i)];
            }
            guardar(CLAVE_AVANCE, JSON.stringify(avance));
            pintar();
          });
          return el("li", { className: avance[clave(seccion, i)] ? "hecho" : "" },
            casilla,
            el("label", { htmlFor: id },
              el("span", { texto: accion }),
              el("small", { texto: "Esperado: " + esperado })));
        }))
        : el("p", { className: "nota", texto: "Todos los pasos de esta sección están verificados." })
    );
  }

  function pintar() {
    const lista = visibles();
    $("indice").replaceChildren(...lista.map((s) => el("a", { href: "#prueba-" + s.id, texto: s.hu })));
    $("secciones").replaceChildren(...lista.map(pintarSeccion));
    pintarAvance();
  }

  $("filtro-rol").addEventListener("change", pintar);
  $("solo-pendientes").addEventListener("change", pintar);
  $("reiniciar").addEventListener("click", () => {
    if (!confirm("¿Borrar el avance de la guía en este navegador?")) {
      return;
    }
    avance = {};
    guardar(CLAVE_AVANCE, "{}");
    pintar();
    avisar("Avance reiniciado.");
  });

  pintar();
})();
