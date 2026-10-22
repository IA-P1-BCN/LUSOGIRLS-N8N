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

- [ ] Un aviso por hito, con importe y fecha reales.
- [ ] Solo activos con fecha límite anterior a hoy se solicitan vencer.
- [ ] Vale y avisos corresponden a la respuesta real; no hay doble notificación.
- [ ] Fallos y ausencia de correo quedan visibles para Marisa.
