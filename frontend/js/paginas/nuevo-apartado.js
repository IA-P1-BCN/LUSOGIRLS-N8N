// Página «Nuevo apartado»: formulario que envía los datos a la API.
// Si la API los rechaza, el formulario sigue como estaba (no se pierde lo escrito).

import { api } from "../api.js";
import { mostrarAviso, montarLayout } from "../layout.js";
import { FORMAS_PAGO, icono, opcionesFormaPago } from "../ui.js";

const principal = montarLayout("apartados");

principal.innerHTML = `
  <div class="page-head">
    <div>
      <a href="/" class="muted">${icono("back", 16)} Apartados</a>
      <h1 style="margin-top:8px">Nuevo apartado</h1>
    </div>
  </div>
  <form id="formulario" class="card card-body">
    <fieldset>
      <legend>Cliente</legend>
      <div class="grid">
        <div><label for="cliente">Nombre <span class="req" aria-hidden="true">*</span></label>
          <input id="cliente" name="cliente" required autocomplete="name" autofocus></div>
        <div><label for="telefono">Teléfono</label>
          <input id="telefono" name="telefono" type="tel" autocomplete="tel"></div>
        <div><label for="email">Correo</label>
          <input id="email" name="email" type="email" autocomplete="email">
          <span class="hint">Para enviarle la confirmación y los recordatorios.</span></div>
      </div>
      <label style="display:flex;align-items:flex-start;gap:10px;margin-top:16px">
        <input style="width:auto;margin-top:4px" type="checkbox" name="consentimiento_notificaciones">
        <span>El cliente ha autorizado recibir por correo las confirmaciones, recibos, recordatorios y avisos de vale de este apartado. Puede retirar la autorización desde el detalle.</span>
      </label>
    </fieldset>
    <fieldset>
      <legend>Zapatos</legend>
      <div class="grid">
        <div><label for="producto">Modelo <span class="req" aria-hidden="true">*</span></label>
          <input id="producto" name="producto" required placeholder="Botín piel marrón"></div>
        <div><label for="talla">Talla</label>
          <input id="talla" name="talla" inputmode="numeric"></div>
        <div><label for="precio">Precio (€) <span class="req" aria-hidden="true">*</span></label>
          <input id="precio" name="precio" type="number" step="0.01" min="0.01" required></div>
      </div>
    </fieldset>
    <fieldset>
      <legend>Pago inicial</legend>
      <div class="grid">
        <div><label for="abono_inicial">Abono inicial (€) <span class="req" aria-hidden="true">*</span></label>
          <input id="abono_inicial" name="abono_inicial" type="number" step="0.01" min="5" required aria-describedby="abono-hint">
          <span class="hint" id="abono-hint">Mínimo 5 €. El resto se paga en un plazo de 3 meses.</span></div>
        <div><label for="forma_pago">Forma de pago</label>
          <select id="forma_pago" name="forma_pago">${opcionesFormaPago(FORMAS_PAGO)}</select></div>
      </div>
    </fieldset>
    <div class="actions">
      <button class="btn btn-primary" type="submit">${icono("plus")} Guardar apartado</button>
      <a class="btn btn-ghost" href="/">Cancelar</a>
    </div>
  </form>`;

document.getElementById("formulario").addEventListener("submit", async (evento) => {
  evento.preventDefault();
  const f = new FormData(evento.target);
  const boton = evento.target.querySelector("button[type=submit]");
  boton.disabled = true;
  try {
    const nuevo = await api.crearApartado({
      cliente: f.get("cliente"),
      telefono: f.get("telefono") || null,
      email: f.get("email") || null,
      consentimiento_notificaciones: f.get("consentimiento_notificaciones") === "on",
      producto: f.get("producto"),
      talla: f.get("talla") || null,
      precio: Number(f.get("precio")),
      abono_inicial: Number(f.get("abono_inicial")),
      forma_pago: f.get("forma_pago"),
    });
    location.href = `/apartados/${nuevo.id}?ok=${encodeURIComponent("Apartado creado")}`;
  } catch (e) {
    mostrarAviso("error", e.message);
    boton.disabled = false;
  }
});
