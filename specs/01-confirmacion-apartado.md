# PF-01 · Confirmación de apartado

## Estado y alcance

Propuesta. [HU-01 / #2](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/2). Autora: Rita; revisora: Fabiana. Entidades: Cliente, Producto, Apartado, Notificación de [la ontología](../docs/ontologia.md).

## Disparador y entradas

Evento `apartado.creado` en PF-00. `datos` es un Apartado: `id`, `cliente`, `producto`, `talla`, `precio`, `abonado`, `pendiente`, `fecha_limite`, `estado`, `email`, `telefono`, `fecha`. No confundir un campo nulo opcional con un fallo de lectura.

## Procesamiento y salidas

Validar campos requeridos y usar literalmente los saldos y fecha límite que entrega la app. Preparar una confirmación con modelo, talla disponible, precio, abonado, pendiente y plazo. Si nació `liquidado`, incluir que puede recogerse. Con email válido, enviar por el canal de correo configurado; si no hay correo, avisar a Marisa sin fallar por ese motivo. Una alternativa Telegram necesita identidad y canal acordados, nunca inferidos del nombre.

No registrar otro abono: el inicial ya está guardado por la app. No esperar `abono.registrado` para ese pago inicial.

## Errores e idempotencia

Campos financieros ausentes: incidencia, sin inventar un saldo. Error del proveedor: PF-08 y recuperación controlada. Clave propuesta del envío `apartado.creado:<id>`, persistida con resultado; una repetición no debe duplicar un envío confirmado. Ante respuesta incierta del proveedor, consultar estado o revisar antes de repetir.

## Credenciales y variables

`PF · Notificaciones`, destino autorizado de Marisa y registro auxiliar de envíos. Canal y cuenta de prueba pendientes; no están conectados por esta spec.

## Pruebas y aceptación

[F01-01, F01-02 y F01-03](../data/pruebas/contratos.json): confirmación completa, correo ausente y evento repetido.

- [ ] Mensaje en menos de un minuto desde la creación en una prueba integrada.
- [ ] Modelo/talla y cifras coinciden con el payload, sin cálculos de IA.
- [ ] Falta de correo: aviso a la tienda y cero envíos al cliente.
- [ ] Evento repetido con envío confirmado: cero mensajes adicionales.
- [ ] JSON importado, evidencia con destino de prueba y revisión en la PR hacia `dev`.
