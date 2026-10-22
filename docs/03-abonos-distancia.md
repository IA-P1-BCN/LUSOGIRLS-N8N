# Configurar y revisar PF-03

El flujo sigue en borrador. Las pruebas de negocio usan datos ficticios, API real aislada, IA simulada y correo local. No publicar hasta validar OpenRouter, el buzón y el recibo PF-02 de Rita.

## Credenciales de cada integrante

Fabiana y Rita comparten el código y los JSON por GitHub. Cada una configura las credenciales en su propia instancia de n8n, con los mismos nombres. No necesitan copiarse sus claves personales ni compartir el `.env`. `localhost` corresponde al ordenador de quien lo abre; los dos n8n no se sincronizan por hacer un push.

| Credencial | Configuración local |
| --- | --- |
| `PF · Modelo extracción` | Header Auth: Name `Authorization`; Value formado por `Bearer`, un espacio y la clave completa de OpenRouter. Guardar solo en n8n. |
| `PF · Buzón de pruebas` | IMAP: servidor, puerto y acceso de un buzón de pruebas. Usar conexión TLS conforme al proveedor. |
| `PF · API tienda` | Header Auth `X-API-Key` con el valor del `.env` de esa instalación. |
| `PF · Notificaciones` | SMTP local de Mailpit, como en [servicios compartidos](automatizaciones-locales.md). |
| `PF · Registro auxiliar` | PostgreSQL del registro auxiliar. |

Una clave llamada «Default key» sirve si está vigente y se copia su valor completo. El nombre de la clave no es el secreto y el valor abreviado de la pantalla no basta. No pegar claves en chat, capturas, JSON ni bitácora. Al importar, seleccionar las credenciales propias por nombre: los IDs de otra instalación no se exportan.

OpenRouter recibe únicamente asunto y cuerpo del correo ficticio. El flujo fija `model: openrouter/free` y `provider.max_price: {prompt: 0, completion: 0}`, sin alternativas de pago. La disponibilidad y los límites gratuitos pueden variar; una indisponibilidad debe generar error, nunca cambiar automáticamente a un modelo de pago. Referencias verificadas el 22/10/2026: [modelos gratuitos](https://openrouter.ai/docs/guides/routing/model-variants/free) y [límite de precio por proveedor](https://openrouter.ai/docs/guides/routing/provider-selection#max-price).

## Preparación del registro y de la entrada

Después de iniciar los servicios compartidos, aplicar la tabla de bloqueos auxiliares (no modifica SQLite):

```bash
docker compose -f docker-compose.yml -f infra/automatizaciones.compose.yml exec -T registro psql -U n8n -d automatizaciones < infra/03-pagos.sql
```

En `pf_config`, revisar `API_BASE_URL`, `MODELO_EXTRACCION=openrouter/free`, `CUENTA_BUZON`, `CORREO_MARISA` y `CORREO_REMITENTE`. `CUENTA_BUZON` identifica la cuenta y debe permanecer estable: cambiarla cambia la clave de deduplicación. Los destinatarios de pruebas deben quedar en Mailpit.

Importar `workflows/03-abonos-distancia.json`, seleccionar las cinco credenciales y asociar PF-08 como Error Workflow. Mantener sin publicar. La entrada IMAP entrega cada correo al procesador del mismo workflow; el nodo Execute Workflow usa el ID de su propia instancia de forma dinámica. No editarlo con un ID del laboratorio.

El mensaje necesita un Message-ID estable. Los nueve `.eml` del proyecto no contienen esa cabecera: el adaptador de pruebas asigna uno ficticio y estable por archivo. Esto no demuestra recepción IMAP real.

## Comprobar y conciliar

Con el laboratorio preparado y PF-08 probado:

```bash
python3 tests/n8n/lab.py 03
python3 tests/n8n/lab.py tests/n8n/test_03_lote.py
```

El test crea una base de datos semilla nueva dentro del volumen aislado para cada ejecución; no borra bases anteriores. La app vuelve a su base de laboratorio habitual al terminar. Las pruebas de timeout conservan reservas y bloqueos como evidencia. No usar los scripts contra producción.

Para una prueba del proveedor real, configurar además `PF · Modelo extracción` en el n8n de laboratorio y registrar **solo su referencia** en `.estado/credentials.json`, bajo ese mismo nombre. Con esa referencia, `PF_TEST_OPENROUTER=1 python3 tests/n8n/lab.py 03` ejecuta los nueve casos y la repetición con el modelo externo. Ese resultado todavía no está disponible; el test no sustituye automáticamente un fallo del proveedor por IA simulada.

Un timeout o una respuesta incierta después de `Registrar abono` deja la reserva del mensaje y el bloqueo del apartado. Repetir el correo no repite el POST. La persona revisora debe contrastar la ejecución, el correo y `GET /api/apartados/{id}`. Si no puede demostrar si el abono se creó, conservar el bloqueo y pedir conciliación; no borrar filas ni cambiar el Message-ID para forzar otro intento. El bloqueo solo coordina PF-03 y no impide que una persona modifique el apartado desde la app.

Un pago aceptado emite el evento normal `abono.registrado`. PF-00 lo entregará a PF-02 cuando Rita lo integre. PF-03 no envía un segundo recibo; la prueba conjunta sigue pendiente.
