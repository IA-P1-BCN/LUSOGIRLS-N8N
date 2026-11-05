# PF-06 · Recordatorios y vencimientos

## Estado y alcance

Propuesta de nivel Medio. [HU-06 / #7](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/7) y [HU-07 / #8](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/8). Autora: Rita; revisora: Fabiana. Separar las dos partes en tareas/PRs si es necesario. Entidades: Apartado, Vale, Notificación.

## Disparadores y entradas

Calendario diario, propuesta 09:00 `Europe/Madrid`. Obtener todos los apartados activos por API y comparar fechas de calendario con `hoy`, fijada al inicio. También consumir `apartado.vencido` desde PF-00 con `datos.apartado` y `datos.vale`.

## Procesamiento y salidas

- Si faltan exactamente 7 o 1 días: enviar recordatorio con saldo y plazo de la app, una vez por hito.
- Si `fecha_limite < hoy`: llamar a `POST /api/apartados/{id}/vencer`; nunca vencer en el propio día límite.
- Tras el vencimiento confirmado, avisar al cliente con código e importe del vale y a Marisa con el modelo/talla para liberar el par. La API no modifica inventario.
- El evento de vencimiento y una conciliación posterior comparten el mismo registro de notificación: evitar enviar una vez desde el calendario y otra desde el Webhook. Conciliar vales sin notificación para recuperar avisos perdidos, porque la app no reintenta.

## Errores e idempotencia

Recordatorio: clave `<apartado_id>:<fecha_limite>:<7|1>:<canal>`. Vencimiento: clave del vale y tipo/destinatario del aviso. Registrar éxito persistente; solo una operación simultánea puede reservar la clave.

Correo ausente: aviso a Marisa sin mensaje al cliente. Si el POST responde `422` porque otro proceso liquidó o venció el apartado, releer y respetar el estado. Ante timeout, consultar detalle/vale antes de repetir. Fallos técnicos a PF-08. Nunca generar el código o importe del vale en n8n.

## Credenciales y variables

API, notificaciones, registro auxiliar, horario y canal acordados. El canal y la identidad del destinatario deben existir; no deducirlos del nombre.

## Pruebas y aceptación

[F06-01 a F06-04](../data/pruebas/contratos.json): 7 días, 1 día con aviso previo, límite hoy y plazo superado con respuesta de la API.

- [x] Un aviso por hito, con importe y fecha reales.
- [x] Solo activos con fecha límite anterior a hoy se solicitan vencer.
- [x] Vale y avisos corresponden a la respuesta real; no hay doble notificación.
- [x] Fallos y ausencia de correo quedan visibles para Marisa.

## Decisiones de implementación · 26/10/2026

Para revisión expresa de Fabiana en la PR de HU-06.

- Dos disparadores en un mismo workflow: `Programar revisión diaria` (cron `0 9 * * *`, `Europe/Madrid`) y `Recibir vencimiento de PF-00` (Execute Workflow Trigger, recibe `{body: {evento, datos}, workflow_id}`). PF-00 lo encuentra con `PF06_WORKFLOW_ID` en `pf_config`.
- `hoy` se fija una vez al inicio en `Europe/Madrid`. Los días restantes se calculan entre fechas de calendario, sin horas.
- Claves de recordatorio: `<apartado_id>:<fecha_limite>:<7|1>:email` para el cliente y `<apartado_id>:<fecha_limite>:<7|1>:marisa` cuando falta el correo.
- Claves de vencimiento: `vale:<codigo>:cliente` y `vale:<codigo>:marisa`. Son las mismas desde el calendario, desde el evento `apartado.vencido` y desde la conciliación, así que solo la primera reserva envía. Esto evita el doble aviso: el controlador `vencer` de la app emite `apartado.vencido` también cuando el vencimiento lo pide PF-06.
- `POST /api/apartados/{id}/vencer` sin reintentos y sin cortar el flujo ante error. Después se relee siempre `GET /api/apartados/{id}` y se decide con su estado: `vencido` con vale avisa, `liquidado` no avisa, `activo` u otro resultado incoherente genera incidencia en PF-08. Cubre el `422` (otro proceso cambió el apartado, o el servidor considera que aún no vence) y el timeout sin repetir el POST.
- Conciliación: cada mañana se leen `GET /api/vales` (la API no filtra) y se concilian los vales de los últimos 7 días de calendario, hoy incluido. Ventana fija decidida por Rita el 26/10/2026 para no avisar de los vales antiguos de los datos de ejemplo.
- El aviso a Marisa se envía siempre tras un vencimiento (liberar el par). Si el cliente no tiene correo, ese mismo aviso lo indica e incluye el teléfono si existe.

## Ampliación HU-14 · 28/10/2026

El correo del cliente exige `consentimiento_notificaciones === true` en el evento/detalle y en `GET /api/apartados/{id}/consentimiento`, consultado antes de reservar el envío con `PF · API tienda`. False/ausente produce aviso a Marisa; una revocación posterior produce un aviso mínimo a la tienda; un error de la consulta impide el envío y activa PF-08. No basta con que exista email. La API actualizada debe desplegarse antes que el flujo. La consulta y SMTP no son una transacción atómica; una revocación simultánea al envío ya iniciado no puede retirarlo.

Modificar el permiso no dispara avisos históricos. Las claves existentes se mantienen; un evento reenviado manualmente con permiso y correo ya válidos puede alcanzar una clave de destinatario aún no confirmada. No usar reenvíos masivos como mecanismo de alta del consentimiento. Pruebas nuevas: [HU-14](../docs/pruebas/14-datos-personales.md); los contratos F01/F02/F06 declaran permiso ficticio explícito para los casos positivos.
