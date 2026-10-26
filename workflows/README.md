# Importar, probar y exportar workflows

Aquí se guardan los JSON de los flujos implementados. PF-08 dispone de exportación y [evidencia de ejecución](../docs/pruebas/08-errores.md). Ver [servicios y laboratorio](../docs/automatizaciones-locales.md) para preparar las credenciales compartidas. Cada nueva PR añade su propio flujo y evidencia.

PF-00 será el único workflow publicado que reciba `POST tienda`. El Webhook inicial de Fabiana (`My workflow`) se conserva **sin publicar**; antes de poner PF-00 en servicio, comprobar que ningún otro workflow publicado use ese método y path. Sus cuatro subflujos reciben `{body: {evento, datos}, workflow_id}` y se seleccionan mediante los IDs de la propia instancia en `pf_config`: ver [spec y tabla de destinos](../specs/00-entrada-eventos.md). No publicar el router hasta integrar y probar los destinos de la pareja.

## Importar en el editor

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

| Uso | Nombre propuesto | Qué configurar fuera de Git |
| --- | --- | --- |
| API de la tienda | `PF · API tienda` | Header Auth, nombre `X-API-Key`, valor del `.env` local |
| Enviar avisos | `PF · Notificaciones` | Cuenta de correo o bot elegido y destino de prueba |
| Leer correo bancario | `PF · Buzón de pruebas` | Acceso Gmail/IMAP a la cuenta de pruebas |
| Extraer datos con IA | `PF · Modelo extracción` | Proveedor y modelo acordados, clave en credenciales |
| Cierres/deduplicación | `PF · Registro auxiliar` | Almacenamiento seleccionado, permisos y claves únicas |

Los nombres son propuestas, no credenciales ya creadas. `UMBRAL_VENTA_GRANDE`, horario, destino de avisos y política de retención se documentan al elegirlos. No depender de una funcionalidad de pago de n8n sin verificar que está disponible en la edición instalada.
