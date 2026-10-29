# PF-01 · Confirmación de apartado

## Estado y alcance

Propuesta. [HU-01 / #2](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/2). Autora: Rita; revisora: Fabiana. Entidades: Cliente, Producto, Apartado, Notificación de [la ontología](../docs/ontologia.md).

## Decisiones de implementación · 23/10/2026

Subworkflow `workflows/01-confirmacion-apartado.json`, llamado por PF-00 con Execute Workflow Trigger y entrada passthrough. Recibe `{body: {evento, datos}, workflow_id}` y lee `body`; su ID se configura en `pf_config` como `PF01_WORKFLOW_ID`. No crea otro Webhook `tienda`.

Correo por SMTP local autorizado (Mailpit). Remitente y destino de la tienda se leen en `pf_config` (`CORREO_REMITENTE`, `CORREO_MARISA`). Reserva atómica en `pf_registro` antes del SMTP y estado `confirmado` después, como PF-04 y PF-08.

Las cifras y la fecha límite se muestran tal como llegan, solo con formato de presentación (dos decimales con coma, fecha dd/mm/aaaa). No se calcula ningún importe ni interviene un modelo de IA. La talla es opcional en la app (`talla: str | None`): si llega vacía o `null`, el mensaje indica «Talla: no indicada» y no se trata como error. El correo se acepta con una comprobación básica de formato: vacío o `null` genera aviso a la tienda con motivo `email_ausente`; un formato no válido, con motivo `email_invalido`.

## Disparador y entradas

Evento `apartado.creado` en PF-00. `datos` es un Apartado: `id`, `cliente`, `producto`, `talla`, `precio`, `abonado`, `pendiente`, `fecha_limite`, `estado`, `email`, `telefono`, `fecha`. No confundir un campo nulo opcional con un fallo de lectura.

## Procesamiento y salidas

Validar campos requeridos y usar literalmente los saldos y fecha límite que entrega la app. Preparar una confirmación con modelo, talla disponible, precio, abonado, pendiente y plazo. Si nació `liquidado`, incluir que puede recogerse. Con email válido, enviar por el canal de correo configurado; si no hay correo, avisar a Marisa sin fallar por ese motivo. Una alternativa Telegram necesita identidad y canal acordados, nunca inferidos del nombre.

No registrar otro abono: el inicial ya está guardado por la app. No esperar `abono.registrado` para ese pago inicial.

## Errores e idempotencia

Campos financieros ausentes: incidencia, sin inventar un saldo. Error del proveedor: PF-08 y recuperación controlada. Claves separadas por destinatario: `apartado.creado:<id>` para la confirmación al cliente y `apartado.creado:<id>:tienda` para el aviso a Marisa cuando falta o no es válido el correo. Así, un aviso a la tienda no impide confirmar al cliente si el apartado se completa después con un correo válido. Cada clave se persiste con su resultado; una repetición no duplica un envío confirmado. Ante respuesta incierta del proveedor, consultar estado o revisar antes de repetir.

## Credenciales y variables

`PF · Registro auxiliar` (`pf_config` y `pf_registro`) y `PF · Notificaciones` (SMTP; Mailpit en local). Destino de la tienda en `CORREO_MARISA`. Cambiar a un proveedor real requiere configuración y autorización del destinatario.

## Pruebas y aceptación

[F01-01, F01-02 y F01-03](../data/pruebas/contratos.json): confirmación completa, correo ausente y evento repetido.

- [x] Mensaje en menos de un minuto desde la creación en una prueba integrada.
- [x] Modelo/talla y cifras coinciden con el payload, sin cálculos de IA.
- [x] Falta de correo: aviso a la tienda y cero envíos al cliente.
- [x] Evento repetido con envío confirmado: cero mensajes adicionales.
- [ ] JSON importado, evidencia con destino de prueba y revisión en la PR hacia `dev`.
