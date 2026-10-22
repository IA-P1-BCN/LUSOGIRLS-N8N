# PF-02 · Recibo de abono

## Estado y alcance

Propuesta. [HU-02 / #3](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/3). Autora: Rita; revisora: Fabiana. Entidades: Apartado, Abono y Notificación.

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

- [ ] Cada abono nuevo produce un recibo con el importe y saldo que da la app.
- [ ] Liquidación: mensaje de recogida y pendiente cero.
- [ ] Repetir el mismo evento no duplica; dos pagos distintos de igual importe sí producen dos recibos.
- [ ] Sin email se avisa a la tienda; errores técnicos quedan trazados sin secretos.
- [ ] Evidencias y JSON exportado revisados por la compañera.
