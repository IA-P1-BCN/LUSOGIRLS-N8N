# PF-02 · Recibo de abono

## Estado y alcance

Propuesta. [HU-02 / #3](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/3). Autora: Rita; revisora: Fabiana. Entidades: Apartado, Abono y Notificación.

## Decisiones de implementación · 26/10/2026

Subworkflow `workflows/02-recibo-abono.json`, llamado por PF-00 con Execute Workflow Trigger y entrada passthrough. Recibe `{body: {evento, datos}, workflow_id}` y lee `body`; su ID se configura en `pf_config` como `PF02_WORKFLOW_ID`. No crea otro Webhook `tienda`. Mismos nodos y patrón que PF-01 y PF-04: `Recibir abono de PF-00`, `Leer configuración`, `Validar abono`, `Reservar operación`, `Comprobar reserva`, `Enviar aviso` y `Confirmar envío`.

Correo por SMTP local autorizado (Mailpit). Remitente y destino de la tienda se leen en `pf_config` (`CORREO_REMITENTE`, `CORREO_MARISA`). Reserva atómica en `pf_registro` antes del SMTP y estado `confirmado` después.

El recibo muestra `importe`, `abonado` y `pendiente` tal como llegan, solo con formato de presentación (dos decimales con coma). No se calcula ningún importe ni interviene un modelo de IA. Los céntimos se obtienen del texto del número, sin multiplicar decimales (mismo método que PF-04), y solo se usan en la clave y en la comprobación de saldo cero.

Claves separadas por destinatario, como en PF-01: `abono.registrado:<apartado_id>:<abonado_en_centimos>:<importe_en_centimos>` para el recibo al cliente y la misma clave con sufijo `:tienda` para el aviso a Marisa. Así, un aviso a la tienda no impide enviar el recibo si una repetición posterior llega con un correo válido.

El aviso a Marisa lleva un motivo: `email_ausente` (vacío o `null`), `email_invalido` (formato no válido) o `saldo_contradictorio` (`estado` `liquidado` con pendiente distinto de cero, o `activo` con pendiente cero). En el último caso no se envía recibo al cliente, no se menciona la recogida y no se corrige el estado: el flujo solo informa de la incoherencia.

Lanzan un error controlado hacia PF-08 (sin recibo): evento distinto de `abono.registrado`, apartado sin `id` válido, datos de cliente o producto ausentes, `importe` ausente o no positivo, datos financieros ausentes, estado distinto de `activo` y `liquidado`, y configuración de correo ausente.

Los nombres `Recibir abono de PF-00` y `Validar abono` deben figurar en la lista de pasos de PF-08 (`workflows/08-errores.json`). Se añaden cuando la PR de HU-01, que modifica esa misma lista, esté integrada en `dev`.

## Disparador y entradas

`abono.registrado` desde PF-00: `datos` contiene el apartado **actualizado** y `importe`, el pago recién recibido. `datos.id` identifica el apartado; el evento no contiene un ID de abono. Fuente: [controlador](../backend/controllers/apartados.py).

## Procesamiento y salidas

Enviar el recibo con `importe`, `abonado` y `pendiente` de la app. Si `estado=liquidado`, añadir el aviso de recogida; si sigue `activo`, indicar lo pendiente. Comprobar coherencia entre `liquidado` y saldo cero; no corregir el estado por cuenta del flujo. Correo ausente: incidencia a Marisa sin fallo por destinatario vacío.

## Errores e idempotencia

Importe ausente, estado desconocido o saldo contradictorio: incidencia sin recibo engañoso. Proveedor caído: PF-08. Clave propuesta `abono.registrado:<apartado_id>:<abonado_en_centimos>:<importe_en_centimos>`; no usar solo `<apartado_id>:<importe>`, porque dos abonos válidos pueden ser iguales. Persistir éxito y coordinar reintentos inciertos con el proveedor.

## Credenciales y variables

`PF · Notificaciones`, destino de Marisa y registro auxiliar, compartidos con PF-01. No requiere escribir en la API de cobros.

## Pruebas y aceptación

[F02-01, F02-02 y F02-03](../data/pruebas/contratos.json): pago parcial, liquidación y dos pagos de igual importe con distinto acumulado.

- [x] Cada abono nuevo produce un recibo con el importe y saldo que da la app.
- [x] Liquidación: mensaje de recogida y pendiente cero.
- [x] Repetir el mismo evento no duplica; dos pagos distintos de igual importe sí producen dos recibos.
- [x] Sin email se avisa a la tienda; errores técnicos quedan trazados sin secretos.
- [ ] Evidencias y JSON exportado revisados por la compañera.
