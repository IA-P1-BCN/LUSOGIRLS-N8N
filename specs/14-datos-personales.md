# HU-14 · Datos personales protegidos

Responsable: Fabiana; revisora: Rita. Trabajo autorizado el 28/10/2026 al pedir completar sus tareas. Esta rama parte de PF-03 (`efe35cf`), aprobada por Rita e integrada mediante la PR #36 en `dev` (`f4e8894`) el 28/10. La nueva minimización requiere su propia validación y revisión.

## Alcance

1. Autenticación Header Auth en los webhooks entregables PF-00 (`tienda`) y PF-09 (`migracion`). El emisor de la app envía `X-PF-Webhook-Key`, configurado mediante `N8N_WEBHOOK_KEY`; n8n usa `PF · Webhook tienda`. Sin clave configurada, el emisor no envía. Las peticiones sin clave o con otra clave se rechazan antes de ejecutar nodos.
2. PF-03 construye una petición mínima: contexto del aviso, ordenante, importe, concepto y medio. No enviar headers/ID de correo, lista de clientes, saldos, contacto, cuenta bancaria, enlaces ni texto ajeno a la extracción. La validación financiera y de identidad continúa localmente y con la API; la IA nunca autoriza un abono. Documentar campos y límites de la reducción.
3. Consentimiento de correo por apartado, explícito y revocable, sin suponer identidad compartida por nombre o email. PF-01/PF-02/PF-06 comprueban consentimiento antes de emitir mensajes al cliente. Los avisos operativos a Marisa se conservan.

## Entidades y API

Apartado incorpora `consentimiento_notificaciones` (booleano, por defecto false) y `consentimiento_actualizado` (fecha/hora UTC o null). La app aplica una migración aditiva al arrancar; los registros existentes quedan false, sin borrar ni recrear tablas. No se concede consentimiento al cargar la semilla.

POST de apartado acepta el booleano opcional, false si se omite. La interfaz muestra una casilla sin marcar. `GET /api/apartados/{id}/consentimiento` devuelve solo ID, permiso y fecha. `PATCH` de esa ruta permite registrar o retirar la autorización declarada por la tienda, con un booleano estricto. Las dos rutas exigen la clave de la API. No se registra un pago ni se reenvían avisos históricos por modificar el permiso.

El detalle permite cambiar la autorización sin editar saldos, pagos ni estado. La fecha deja constancia del cambio registrado; no se atribuye una firma o identidad verificada al cliente.

## Notificaciones

Un evento sin consentimiento o con false no habilita correo al cliente. Cuando el evento/contexto permite correo, se vuelve a consultar la API justo antes de enviar para detectar revocaciones posteriores. Si la consulta falla, el envío falla cerrado y se avisa mediante PF-08. Si el permiso se retiró, se sustituye por un aviso operativo mínimo a Marisa; nunca se manda al cliente.

Las claves de deduplicación de los eventos/hitos se conservan. Conceder consentimiento después de una notificación omitida no dispara automáticamente mensajes históricos. Los futuros bots de Rita deberán aplicar sus controles de identidad y permiso; no se presentan como implementados aquí.

## Credenciales y compatibilidad

`N8N_WEBHOOK_KEY` no se entrega al navegador, no se registra y no se versiona. Debe coincidir con la credencial Header Auth de n8n, cabecera `X-PF-Webhook-Key`. Se configura coordinadamente app/PF-00 antes de activar. API y webhook tienen secretos distintos en una instancia real. Un fallo del webhook no revierte las operaciones de tienda ni autoriza un reintento automático de un pago.

La app existente usa una clave compartida de API y carece de login de usuarios: sigue siendo una aplicación local. La publicación en Internet requiere resolver ese acceso en HU-16; proteger n8n no convierte la interfaz actual en una app pública con autenticación.

## Pruebas de aceptación

- Webhooks sin clave/clave errónea rechazados; clave correcta procesa el evento real enviado por la app; ningún secreto aparece en respuesta pública/log.
- Base antigua conserva datos y obtiene permiso false; alta sin permiso/alta con permiso/revocación y acceso sin autenticación comprobados por API.
- PF-01, PF-02 y PF-06: clientes autorizados reciben; no autorizados y eventos antiguos tras revocar no reciben; los avisos de tienda se mantienen.
- Petición a IA inspeccionada con datos ficticios de teléfono/email/IBAN/enlaces: solo campos necesarios salen, sin lista de clientes ni saldos. Mantener y probar los nueve correos de HU-03.
- JSON finales importados/exportados inactivos; credenciales por nombre y evidencias reales antes de solicitar aprobación a Rita.
