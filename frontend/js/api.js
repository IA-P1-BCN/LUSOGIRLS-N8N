// Comunicación con la API. La interfaz habla con el servidor SOLO por aquí,
// con la misma cabecera X-API-Key que usa n8n.

const CLAVE = window.APP_CONFIG?.apiKey ?? "";

export class ErrorApi extends Error {
  constructor(mensaje, estado) {
    super(mensaje);
    this.estado = estado;
  }
}

async function pedir(ruta, opciones = {}) {
  const cabeceras = { "X-API-Key": CLAVE };
  if (opciones.body) cabeceras["Content-Type"] = "application/json";
  let respuesta;
  try {
    respuesta = await fetch(ruta, { ...opciones, headers: cabeceras });
  } catch {
    throw new ErrorApi("No se puede conectar con el servidor. ¿Está encendido?", 0);
  }
  if (!respuesta.ok) {
    let detalle = `Error ${respuesta.status}`;
    try {
      const cuerpo = await respuesta.json();
      // Errores de negocio: texto. Errores de validación de Pydantic: lista de {loc, msg}.
      detalle = Array.isArray(cuerpo.detail) ? cuerpo.detail.map((d) => `${d.loc.at(-1)}: ${d.msg}`).join(". ") : cuerpo.detail;
    } catch {}
    throw new ErrorApi(detalle, respuesta.status);
  }
  return respuesta;
}

const consulta = (parametros) => {
  const q = new URLSearchParams();
  for (const [clave, valor] of Object.entries(parametros)) if (valor !== undefined && valor !== null && valor !== "") q.set(clave, valor);
  const texto = q.toString();
  return texto ? `?${texto}` : "";
};

export const api = {
  async apartados({ estado, q, pagina, porPagina = 25 } = {}) {
    const r = await pedir(`/api/apartados${consulta({ estado, q, pagina, por_pagina: porPagina })}`);
    return { items: await r.json(), total: Number(r.headers.get("X-Total-Count")) };
  },
  async resumen() {
    return (await pedir("/api/apartados/resumen")).json();
  },
  async apartado(id) {
    return (await pedir(`/api/apartados/${id}`)).json();
  },
  async crearApartado(datos) {
    return (await pedir("/api/apartados", { method: "POST", body: JSON.stringify(datos) })).json();
  },
  async registrarAbono(id, datos) {
    return (await pedir(`/api/apartados/${id}/abonos`, { method: "POST", body: JSON.stringify(datos) })).json();
  },
  async cambiarConsentimiento(id, autorizado) {
    return (await pedir(`/api/apartados/${id}/consentimiento`, {
      method: "PATCH", body: JSON.stringify({ consentimiento_notificaciones: autorizado }),
    })).json();
  },
  async ventas({ pagina, porPagina = 25 } = {}) {
    const r = await pedir(`/api/ventas${consulta({ orden: "desc", pagina, por_pagina: porPagina })}`);
    return { items: await r.json(), total: Number(r.headers.get("X-Total-Count")) };
  },
  async registrarVenta(datos) {
    return (await pedir("/api/ventas", { method: "POST", body: JSON.stringify(datos) })).json();
  },
  async descargarExcel() {
    const r = await pedir("/api/excel");
    const enlace = document.createElement("a");
    enlace.href = URL.createObjectURL(await r.blob());
    enlace.download = `paso-firme-${new Date().toISOString().slice(0, 10)}.xlsx`;
    enlace.click();
    URL.revokeObjectURL(enlace.href);
  },
};
