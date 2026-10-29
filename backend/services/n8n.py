"""SERVICIO · Avisar a n8n por webhook cuando pasa algo en la tienda."""

import json
import logging
import urllib.request

import config

log = logging.getLogger("tienda")


class _SinRedirecciones(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_cliente_http = urllib.request.build_opener(_SinRedirecciones())


def avisar(evento, datos):
    """Envía el evento a n8n. Si n8n no responde, la tienda sigue funcionando."""
    if not config.N8N_WEBHOOK_URL:
        return
    if not config.N8N_WEBHOOK_KEY:
        log.warning('No se pudo avisar a n8n (%s): falta configurar la autenticación', evento)
        return
    cuerpo = json.dumps({"evento": evento, "datos": datos}, default=str).encode()
    peticion = urllib.request.Request(config.N8N_WEBHOOK_URL, cuerpo,
                                     {"Content-Type": "application/json", "X-PF-Webhook-Key": config.N8N_WEBHOOK_KEY})
    try:
        with _cliente_http.open(peticion, timeout=5):
            pass
    except Exception:
        # La excepción de transporte puede contener URLs o cabeceras; no registrarla.
        log.warning("No se pudo avisar a n8n (%s): fallo de entrega", evento)
