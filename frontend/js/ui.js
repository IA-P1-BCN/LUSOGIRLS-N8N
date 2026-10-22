// Piezas de interfaz reutilizables: iconos, importes, etiquetas y paginación.
// Todo lo que viene de la API y se pinta pasa por esc() para que no se pueda inyectar HTML.

export const esc = (texto) =>
  String(texto ?? "").replace(/[&<>"']/g, (c) => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[c]);

// Iconos (Lucide, licencia MIT)
const ICONOS = {
  plus: '<path d="M5 12h14"/><path d="M12 5v14"/>',
  search: '<circle cx="11" cy="11" r="8"/><path d="m21 21-4.3-4.3"/>',
  apartados: '<rect width="8" height="4" x="8" y="2" rx="1"/><path d="M16 4h2a2 2 0 0 1 2 2v14a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2V6a2 2 0 0 1 2-2h2"/><path d="M12 11h4"/><path d="M12 16h4"/><path d="M8 11h.01"/><path d="M8 16h.01"/>',
  ventas: '<path d="M4 2v20l2-1 2 1 2-1 2 1 2-1 2 1 2-1 2 1V2l-2 1-2-1-2 1-2-1-2 1-2-1-2 1Z"/><path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/><path d="M12 17.5v-11"/>',
  excel: '<path d="M15 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V7Z"/><path d="M14 2v4a2 2 0 0 0 2 2h4"/><path d="M8 13h2"/><path d="M14 13h2"/><path d="M8 17h2"/><path d="M14 17h2"/>',
  api: '<polyline points="16 18 22 12 16 6"/><polyline points="8 6 2 12 8 18"/>',
  logo: '<path d="M4 16v-2.38C4 11.5 2.97 10.5 3 8c.03-2.72 1.49-6 4.5-6C9.37 2 10 3.8 10 5.5c0 3.11-2 5.66-2 8.68V16a2 2 0 1 1-4 0Z"/><path d="M20 20v-2.38c0-2.12 1.03-3.12 1-5.62-.03-2.72-1.49-6-4.5-6C14.63 6 14 7.8 14 9.5c0 3.11 2 5.66 2 8.68V20a2 2 0 1 0 4 0Z"/><path d="M16 17h4"/><path d="M4 13h4"/>',
  prev: '<path d="m15 18-6-6 6-6"/>',
  next: '<path d="m9 18 6-6-6-6"/>',
  back: '<path d="m12 19-7-7 7-7"/><path d="M19 12H5"/>',
  ok: '<circle cx="12" cy="12" r="10"/><path d="m9 12 2 2 4-4"/>',
  alert: '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3"/><path d="M12 9v4"/><path d="M12 17h.01"/>',
  vale: '<path d="M2 9a3 3 0 0 1 0 6v2a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-2a3 3 0 0 1 0-6V7a2 2 0 0 0-2-2H4a2 2 0 0 0-2 2Z"/><path d="M13 5v2"/><path d="M13 17v2"/><path d="M13 11v2"/>',
};

export const icono = (nombre, tam = 18) =>
  `<svg class="icon" width="${tam}" height="${tam}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${ICONOS[nombre]}</svg>`;

const formato = new Intl.NumberFormat("es-ES", { minimumFractionDigits: 2, maximumFractionDigits: 2, useGrouping: "always" });
export const euros = (n) => `${formato.format(n)} €`;

const capitalizar = (t) => t.charAt(0).toUpperCase() + t.slice(1);
export const etiquetaEstado = (estado) => `<span class="badge badge-${esc(estado)}">${esc(capitalizar(estado))}</span>`;

// Días que faltan hasta una fecha "AAAA-MM-DD" (negativo si ya pasó)
export function diasHasta(fecha) {
  const hoy = new Date();
  const inicioHoy = new Date(hoy.getFullYear(), hoy.getMonth(), hoy.getDate());
  return Math.round((new Date(`${fecha}T00:00:00`) - inicioHoy) / 86400000);
}

export function plazo(apartado) {
  if (apartado.estado !== "activo") return '<span class="muted">—</span>';
  const d = diasHasta(apartado.fecha_limite);
  if (d < 0) return `<span class="badge badge-danger">${icono("alert", 14)} Fuera de plazo (${-d} ${d === -1 ? "día" : "días"})</span>`;
  if (d === 0) return `<span class="badge badge-warn">${icono("alert", 14)} Vence hoy</span>`;
  if (d === 1) return '<span class="badge badge-warn">Vence mañana</span>';
  if (d <= 7) return `<span class="badge badge-warn">Vence en ${d} días</span>`;
  return `<span class="muted">Quedan ${d} días</span>`;
}

export function paginacion(pagina, paginas, total, base) {
  if (paginas <= 1) return "";
  const anterior = pagina > 1 ? `<a class="btn btn-ghost" href="${base}pagina=${pagina - 1}">${icono("prev")} Anterior</a>` : "";
  const siguiente = pagina < paginas ? `<a class="btn btn-ghost" href="${base}pagina=${pagina + 1}">Siguiente ${icono("next")}</a>` : "";
  return `<nav class="pager" aria-label="Paginación">
    <span class="muted">Página ${pagina} de ${paginas} · ${total} en total</span>
    <div class="pager-buttons">${anterior}${siguiente}</div></nav>`;
}

export const opcionesFormaPago = (formas, actual = "efectivo") =>
  formas.map((f) => `<option value="${esc(f)}" ${f === actual ? "selected" : ""}>${esc(capitalizar(f))}</option>`).join("");

export const FORMAS_PAGO = ["efectivo", "tarjeta", "bizum", "transferencia"];

export function alerta(tipo, texto) {
  const clase = tipo === "error" ? "alert-error" : "alert-ok";
  const rol = tipo === "error" ? "alert" : "status";
  return `<div class="alert ${clase}" role="${rol}">${icono(tipo === "error" ? "alert" : "ok")} <span>${esc(texto)}</span></div>`;
}
