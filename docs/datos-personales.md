# HU-14 · Datos personales y permisos de correo

La app registra permiso por apartado. La casilla de alta está desmarcada; en el detalle se puede registrar o retirar la autorización declarada por el cliente. No se infiere por nombre, dirección de correo ni teléfono. La migración del esquema conserva los datos anteriores y los deja sin autorización. El permiso de correo no autoriza Telegram ni acredita una identidad verificada.

## Preparación de la instancia

1. Actualizar la app. El arranque añade `consentimiento_notificaciones` y `consentimiento_actualizado` sin recrear la base. Comprobar en `/docs` las rutas `GET/PATCH /api/apartados/{id}/consentimiento`; ambas requieren `X-API-Key`.
2. Crear **PF · Webhook tienda**, tipo Header Auth, nombre de cabecera **X-PF-Webhook-Key**. Guardar su valor solo en la credencial y en `N8N_WEBHOOK_KEY` del `.env` de la app. Usar un secreto distinto de `API_KEY`. No copiar valores en Git, navegador, `pf_config`, capturas o comandos compartidos.
3. Importar PF-00 y PF-09 sin publicar. Abrir sus nodos Webhook y seleccionar expresamente **PF · Webhook tienda**. La API usa otra credencial Header Auth: comprobar que n8n no ha seleccionado **PF · API tienda** por similitud de tipo.
4. Importar PF-01/PF-02/PF-06 y seleccionar **PF · API tienda** en `Consultar consentimiento actual`. Seleccionar las credenciales PostgreSQL/SMTP y PF-08 como Error Workflow. Configurar los IDs locales en `pf_config`.
5. Probar sin clave, con clave errónea y con la correcta. Probar altas sin permiso, con permiso y después de revocar. Los fallos del webhook no revierten cobros ni habilitan repetir un POST de negocio.

PF-00 y PF-09 se entregan con `saveDataSuccessExecution=none`, `saveDataErrorExecution=none`, `saveManualExecutions=false` y `saveExecutionProgress=false`: el nodo Webhook recibe la cabecera secreta, por lo que no se conserva su historial. La trazabilidad funcional permanece en los subflujos y el registro auxiliar. Solo copias aisladas con datos ficticios habilitan historial para obtener evidencias. No activar ese modo de prueba con información real.

## Qué se envía al modelo en PF-03

| Campo | Contenido y finalidad |
| --- | --- |
| Instrucción fija y esquema JSON | Define extracción, campos permitidos y prohibición de inventar identidades, saldos o pagos. |
| Contexto del asunto | Etiqueta derivada de un asunto bancario reconocido: aviso Bizum o transferencia. No se envía el asunto original completo. |
| Ordenante | Nombre o abreviatura literal, máximo 200 caracteres; necesario para proponer un candidato. Sigue siendo un dato personal. |
| Importe | Valor numérico literal en EUR; no se envía el saldo de la app. |
| Concepto | Texto de la línea concepto, máximo 500 caracteres; puede contener la referencia de apartado o producto. |

No se envían el correo completo, remitente/destinatario, Message-ID, adjuntos, listado de clientes, saldos ni detalles de la API. En los campos de texto se ocultan patrones de email, URL HTTP(S), IBAN y secuencias numéricas largas compatibles con teléfonos o tarjetas. Esto reduce datos; no garantiza anonimato ni detecta toda información personal escrita libremente en un concepto. Solo se han usado datos ficticios en las pruebas.

Los formatos bancarios admitidos son los de los nueve `.eml` del repositorio. Un asunto desconocido que incluye campos de pago produce un error controlado antes de llamar al proveedor. La validación posterior conserva el original local y compara la extracción con él; si el recorte u ocultación afecta un dato necesario, falla para revisión sin registrar un abono. La IA no recibe acceso a la tienda ni decide si se cobra. El enrutador gratuito mantiene coste máximo cero; puede rechazar temporalmente llamadas por disponibilidad o cuota.

## Avisos y límites

PF-01/PF-02/PF-06 exigen booleano `true` en el evento/detalle y vuelven a consultar el permiso vigente antes de reservar el envío. Una revocación produce aviso operativo mínimo a Marisa; una consulta fallida impide el correo al cliente y activa PF-08. Los avisos a la tienda mantienen su función operativa. Cambiar el permiso no dispara mensajes históricos ni modifica pagos o saldos.

La consulta y el envío SMTP no son atómicos: una revocación simultánea a un envío ya iniciado no puede retirarlo. El registro auxiliar de deduplicación conserva documentos de notificación; su acceso y retención, y el acceso al buzón y al editor n8n, deben gestionarse en la instancia. Esta entrega no declara cumplimiento legal integral ni publicación en Internet.

La app local todavía expone una clave compartida de API a su interfaz y no tiene login de personas. Proteger el webhook no resuelve ese acceso: una publicación en nube requiere autenticación de la app y la configuración acordada en HU-16.

Fuentes: [spec](../specs/14-datos-personales.md), [evidencias](pruebas/14-datos-personales.md) y [ajustes de redacción de n8n](https://docs.n8n.io/deploy/host-n8n/configure-n8n/security/redact-execution-data). No se depende de la función Enterprise de redacción; se desactiva la persistencia de los dos webhooks.
