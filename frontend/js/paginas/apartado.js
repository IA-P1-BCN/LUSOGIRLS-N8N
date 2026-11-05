// Página de un apartado: resumen, barra de progreso, abonos, vale (si venció) y formulario para abonar.

import { api } from "../api.js";
import { avisoDeLaDireccion, mostrarAviso, montarLayout } from "../layout.js";
import { FORMAS_PAGO, diasHasta, esc, euros, etiquetaEstado, icono, opcionesFormaPago, plazo } from "../ui.js";

const principal = montarLayout("apartados");
const id = location.pathname.split("/").pop();
const capitalizar = (t) => t.charAt(0).toUpperCase() + t.slice(1);

function panelDeAbono(a) {
  if (a.estado !== "activo") return "";
  if (diasHasta(a.fecha_limite) < 0) {
    return `<div class="card card-body"><div class="alert alert-error" style="margin:0">${icono("alert")} <span>Este apartado está fuera de plazo y no admite más abonos. Hay que vencerlo para generar el vale.</span></div></div>`;
  }
  return `<form id="formulario-abono" class="card card-body stack" aria-label="Registrar abono">
    <h2>Registrar abono</h2>
    <div><label for="importe">Importe (€)</label>
      <input id="importe" name="importe" type="number" step="0.01" min="0.01" max="${a.pendiente}" required autofocus aria-describedby="importe-hint">
      <span class="hint" id="importe-hint">Faltan ${euros(a.pendiente)}.</span></div>
    <div><label for="forma_pago">Forma de pago</label>
      <select id="forma_pago" name="forma_pago">${opcionesFormaPago(FORMAS_PAGO)}</select></div>
    <button class="btn btn-primary" type="submit">Registrar abono</button>
  </form>`;
}

async function pintar() {
  const a = await api.apartado(id);
  const abonos = [...a.abonos].reverse(); // el más reciente primero
  const porcentaje = Math.round((a.abonado / a.precio) * 100);
  const contacto = [a.telefono, a.email].filter(Boolean).join(" · ") || "Sin datos de contacto";
  document.title = `Apartado #${a.id} · Paso Firme`;
  principal.innerHTML = `
    <div class="page-head">
      <div>
        <a href="/" class="muted">${icono("back", 16)} Apartados</a>
        <h1 style="margin-top:8px">Apartado #${a.id} ${etiquetaEstado(a.estado)}</h1>
      </div>
    </div>
    <div class="layout-2">
      <div class="stack">
        <section class="card card-body stack" aria-label="Resumen">
          <div>
            <h2>${esc(a.cliente)}</h2>
            <p class="muted" style="margin:4px 0 0">${esc(contacto)}</p>
          </div>
          <p style="margin:0"><strong>${esc(a.producto)}</strong>${a.talla ? ` · Talla ${esc(a.talla)}` : ""}</p>
          <div class="stats">
            <div class="stat"><div class="label">Precio</div><div class="value">${euros(a.precio)}</div></div>
            <div class="stat"><div class="label">Pagado</div><div class="value">${euros(a.abonado)}</div></div>
            <div class="stat"><div class="label">Pendiente</div><div class="value">${euros(a.pendiente)}</div></div>
          </div>
          <div>
            <div class="progress" role="progressbar" aria-valuenow="${porcentaje}" aria-valuemin="0" aria-valuemax="100" aria-label="Pagado"><span style="width: ${porcentaje}%"></span></div>
            <p class="muted" style="margin:6px 0 0">${porcentaje}% pagado · Apartado el ${esc(a.fecha)} · Fecha límite ${esc(a.fecha_limite)} ${plazo(a)}</p>
          </div>
          ${a.vale ? `<div class="alert alert-ok" style="margin:0">${icono("vale")} <span>Vale de compra <strong>${esc(a.vale.codigo)}</strong> por ${euros(a.vale.importe)}${a.vale.usado ? " (usado)" : ""}</span></div>` : ""}
          <form id="formulario-consentimiento" class="stack" aria-label="Permiso de notificaciones">
            <h3>Notificaciones por correo</h3>
            <label style="display:flex;align-items:flex-start;gap:10px">
              <input style="width:auto;margin-top:4px" type="checkbox" name="autorizado" ${a.consentimiento_notificaciones ? "checked" : ""}>
              <span>El cliente autoriza los avisos de este apartado.</span>
            </label>
            <span class="hint">${a.consentimiento_actualizado ? `Permiso actualizado: ${esc(new Date(a.consentimiento_actualizado).toLocaleString("es-ES"))}.` : "No se ha registrado autorización."} Guardar el permiso no reenvía mensajes anteriores.</span>
            <button type="submit" class="btn btn-ghost">Guardar permiso</button>
          </form>
        </section>
        <section class="card" aria-label="Abonos">
          <div class="card-body" style="padding-bottom:0"><h2>Abonos</h2></div>
          <div class="table-wrap">
            <table>
              <thead><tr><th>Fecha</th><th>Forma de pago</th><th class="num">Importe</th></tr></thead>
              <tbody>${abonos.map((b) => `<tr><td>${esc(b.fecha)}</td><td>${esc(capitalizar(b.forma_pago))}</td><td class="num">${euros(b.importe)}</td></tr>`).join("")}</tbody>
            </table>
          </div>
        </section>
      </div>
      ${panelDeAbono(a)}
    </div>`;
  document.getElementById("formulario-abono")?.addEventListener("submit", registrar);
  document.getElementById("formulario-consentimiento").addEventListener("submit", async (evento) => {
    evento.preventDefault();
    const boton = evento.target.querySelector("button[type=submit]");
    boton.disabled = true;
    try {
      await api.cambiarConsentimiento(id, new FormData(evento.target).get("autorizado") === "on");
      await pintar();
      mostrarAviso("ok", "Permiso de notificaciones actualizado");
    } catch (e) {
      mostrarAviso("error", e.message);
      boton.disabled = false;
    }
  });
  avisoDeLaDireccion();
}

async function registrar(evento) {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const boton = evento.target.querySelector("button[type=submit]");
  boton.disabled = true;
  try {
    const actualizado = await api.registrarAbono(id, { importe: Number(f.get("importe")), forma_pago: f.get("forma_pago") });
    const mensaje = actualizado.estado === "liquidado" ? "Apartado liquidado: ya puede recoger sus zapatos" : "Abono registrado";
    location.href = `/apartados/${id}?ok=${encodeURIComponent(mensaje)}`;
  } catch (e) {
    mostrarAviso("error", e.message);
    boton.disabled = false;
  }
}

pintar().catch((e) => mostrarAviso("error", e.message));
