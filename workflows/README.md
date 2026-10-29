# Importar, probar y exportar workflows

Aquí se guardan los JSON de los flujos implementados. PF-08 dispone de exportación y [evidencia de ejecución](../docs/pruebas/08-errores.md). Ver [servicios y laboratorio](../docs/automatizaciones-locales.md) para preparar las credenciales compartidas. Cada nueva PR añade su propio flujo y evidencia.

PF-00 será el único workflow publicado que reciba `POST tienda`. El Webhook inicial de Fabiana (`My workflow`) se conserva **sin publicar**; antes de poner PF-00 en servicio, comprobar que ningún otro workflow publicado use ese método y path. Sus cuatro subflujos reciben `{body: {evento, datos}, workflow_id}` y se seleccionan mediante los IDs de la propia instancia en `pf_config`: ver [spec y tabla de destinos](../specs/00-entrada-eventos.md). No publicar el router hasta integrar y probar los destinos de la pareja.

## Importar en el editor

Para HU-13/PF-12, seguir además [la configuración de la fuente CSV y del registro de datáfono](../docs/12-ventas-datafono.md). La fuente CSV tiene una credencial Header Auth propia, distinta de la API de la tienda.

1. Leer la spec y los requisitos de credenciales del flujo.
2. Abrir n8n local, crear un workflow y elegir en el menú del workflow **Import from File**. Seleccionar el JSON de esta carpeta.
3. Mantenerlo sin publicar. Revisar los nodos y seleccionar las credenciales **de tu propia instancia**. Los IDs de credenciales de otro equipo no garantizan una conexión válida.
4. Configurar URL interna de la app `http://tienda:8000`, zona `Europe/Madrid`, destino de prueba y almacenamiento auxiliar acordado.
5. Ejecutar los casos de su spec; guardar resultados reales. Revisar el Error Workflow asociado.

## Exportar y revisar

En el menú del workflow elegir **Download** y guardar como `workflows/NN-nombre-del-flujo.json`. Revisar antes de hacer commit: parámetros, cabeceras importadas, nombres de credenciales, `pinData`, ejemplos y datos de ejecución. Conservar solo datos ficticios; nunca claves ni mensajes reales.

Alternativa de exportación con el Server CLI disponible en este Docker (sustituir el ID y el nombre de destino):

```bash
ID_FLUJO='ID-del-workflow'
docker compose exec -T n8n n8n export:workflow --id="$ID_FLUJO" --output=/tmp/flujo.json --pretty
docker compose cp n8n:/tmp/flujo.json workflows/01-confirmacion-apartado.json
```

Esta exportación puede ser un array de workflows, mientras que la descarga desde el editor puede ser un objeto. Inspeccionar el contenido y verificar la importación; no crear IDs ni inventar nodos para «completar» un JSON.

La PR incluye el JSON realmente exportado, la spec, los casos y evidencia. La revisora importa el archivo, valida credenciales por referencia y repite las pruebas. No exportar credenciales para incluirlas en Git.

Referencia: [importar y exportar en n8n](https://docs.n8n.io/workflows/export-import/) y [Server CLI](https://docs.n8n.io/hosting/cli-commands/).

## Webhook: probar y publicar son acciones distintas

| Uso | Desde el ordenador | Desde la app en Docker |
| --- | --- | --- |
| Prueba con listener abierto | `http://localhost:5678/webhook-test/tienda` | `http://n8n:5678/webhook-test/tienda` |
| Flujo publicado | `http://localhost:5678/webhook/tienda` | `http://n8n:5678/webhook/tienda` |

Para una prueba manual, pulsar **Listen for test event** y enviar un payload ficticio a la URL de test. No enviar el envoltorio de los contratos: solo su campo `input.payload`. En la salida del nodo se encontrará dentro de `body`. Al usar datos fijados directamente en la salida del nodo, fijar `{"body": <payload>}`.

Para probar desde la app con un workflow sin publicar, cambiar **localmente** `N8N_WEBHOOK_URL` a la URL de test y aplicar con `docker compose up -d tienda`. Después de una publicación expresamente autorizada, volver a `/webhook/tienda`. Si el flujo no está publicado y la app apunta a producción, ese evento puede perderse: la app no reintenta.

## Credenciales y configuración pendientes

| Uso | Nombre compartido | Qué configurar fuera de Git |
| --- | --- | --- |
| API de la tienda | `PF · API tienda` | Header Auth, nombre `X-API-Key`, valor del `.env` local |
| Enviar avisos | `PF · Notificaciones` | Cuenta de correo o bot elegido y destino de prueba |
| Leer correo bancario | `PF · Buzón de pruebas` | Acceso Gmail/IMAP a la cuenta de pruebas |
| Extraer datos con IA | `PF · Modelo extracción` | Credencial nativa OpenRouter (`openRouterApi`), clave en API Key; ver [configuración PF-03](../docs/03-abonos-distancia.md) |
| Cierres/deduplicación | `PF · Registro auxiliar` | Almacenamiento seleccionado, permisos y claves únicas |

Son nombres comunes para que cada integrante cree y seleccione sus credenciales locales; no implican que ya estén configuradas en ambas instancias. No compartir claves personales ni el `.env` por GitHub. `UMBRAL_VENTA_GRANDE`, horario, destino de avisos y política de retención se documentan al elegirlos. No depender de una funcionalidad de pago de n8n sin verificar que está disponible en la edición instalada.

## HU-14: configuración coordinada

Antes de activar PF-00/PF-09, crear `PF · Webhook tienda` de tipo Header Auth con nombre de cabecera `X-PF-Webhook-Key`. Guardar su valor solo en la credencial y en `N8N_WEBHOOK_KEY` del `.env` de la app; debe ser distinto de `API_KEY`. Nunca ponerlo en frontend o `pf_config`. Ambos workflows se entregan sin historial de ejecución para no persistir la cabecera.

PF-01/PF-02/PF-06 necesitan también `PF · API tienda` para consultar el permiso vigente. Actualizar primero la app con su migración aditiva. Los apartados existentes permanecen sin consentimiento hasta que la tienda registre una autorización real. Guía: [datos personales](../docs/datos-personales.md).

## Puesta en marcha: errores frecuentes

Observados al levantar una instancia local con `dev` en `613a23c` y n8n 2.45.4 (`docs/pruebas/2026-10-29-instancia-local-hu14.md`).

- **Subflujos sin publicar.** PF-00, PF-01 y PF-02 (y PF-04 y PF-06 si se usan) deben estar publicados. Si falta uno, PF-00 falla con «Workflow is not active and cannot be executed» y PF-08 avisa del paso `Ejecutar PF-01` (o el que corresponda).
- **Credencial del Webhook.** Crear `PF · Webhook tienda` antes de importar `workflows/00-entrada-eventos.json` y `workflows/09-migracion.json`, como indica [HU-14: configuración coordinada](#hu-14-configuración-coordinada); su valor es igual a `N8N_WEBHOOK_KEY` del `.env`. Después, abrir `Recibir eventos` y `Recibir migración` y comprobar que usan esa credencial y no `PF · API tienda`.
- **Importar sobre un flujo existente.** Vaciar antes el lienzo (Ctrl/Cmd+A y Supr). Si no, los nodos importados se pegan junto a los antiguos.
- **URL del webhook.** Con PF-00 publicado, `N8N_WEBHOOK_URL=http://n8n:5678/webhook/tienda`; con el listener de prueba, `http://n8n:5678/webhook-test/tienda`. Ver [Webhook: probar y publicar son acciones distintas](#webhook-probar-y-publicar-son-acciones-distintas).
- **Sin clave no hay eventos.** Si `N8N_WEBHOOK_KEY` está vacía, la app no envía ningún evento y deja en el log de `tienda` «No se pudo avisar a n8n (…): falta configurar la autenticación» (`backend/services/n8n.py`).
- **Error Workflow.** Los JSON se exportan sin `errorWorkflow`. Elegir PF-08 a mano en **Settings → Error Workflow** de cada flujo de negocio, nunca en el propio PF-08.
- **PF-06.** Publicarlo activa su calendario diario (`0 9 * * *`, 09:00 Europe/Madrid), que vence por API los apartados fuera de plazo y la app genera sus vales. Sin publicarlo, un evento `apartado.vencido` falla en PF-00 con el mismo error que PF-01 sin publicar, y avisa PF-08. Para probarlo sin publicar, ejecutarlo a mano.
