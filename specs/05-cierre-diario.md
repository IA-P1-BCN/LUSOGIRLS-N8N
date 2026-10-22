# PF-05 · Cierre diario

## Estado y alcance

Propuesta. [HU-04 / #5](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/5). Autora: Fabiana; revisora: Rita. Entidades: Venta, Abono, CierreDiario.

## Disparador y entradas

Schedule Trigger. Propuesta a confirmar: 00:05 en `Europe/Madrid`, para cerrar el día anterior completo. Fijar `fecha_cierre` al iniciar. Consultar `GET /api/ventas?desde=D&hasta=D` y `GET /api/abonos?desde=D&hasta=D`. Sin `pagina` la API devuelve todos; si se pagina, recorrer hasta completar `X-Total-Count`.

## Procesamiento y salidas

Sumar por `efectivo`, `tarjeta`, `bizum`, separando ventas directas y abonos y calculando el total. Usar céntimos/decimal, nunca IA para las sumas. Los abonos iniciales ya están en `/api/abonos`; no volver a sumarlos a partir de los apartados.

Guardar un cierre con clave única `fecha_cierre` en el registro auxiliar y enviar el resumen a Marisa. Un día vacío produce un cierre con ceros y «sin movimientos». El guardado y el envío tienen estados separados para recuperar un fallo sin duplicar la fila.

## Errores e idempotencia

Si falla una consulta, no enviar un total parcial como cierre completo. GET puede reintentarse de forma acotada; fallo persistente a PF-08. Upsert por fecha y control de concurrencia. Repetir una fecha ya cerrada no crea otra fila ni reenvía un aviso confirmado; una corrección posterior debe identificarse como tal y revisarse.

## Credenciales y variables

`PF · API tienda`, `PF · Registro auxiliar`, `PF · Notificaciones`, horario confirmado y destino de Marisa. El cierre no tiene endpoint propio en la app.

## Pruebas y aceptación

[F05-01, F05-02 y F05-03](../data/pruebas/contratos.json): importes por medio, día vacío y fallo parcial de API.

- [ ] Cada fecha produce ventas, abonos y total exactos por medio y globalmente.
- [ ] Día vacío: ceros y aviso explícito, sin error.
- [ ] Repetición: una fila por fecha y ningún aviso confirmado duplicado.
- [ ] Fallo de fuente: no guardar/enviar un cierre completo incorrecto.
- [ ] Caso manual con datos ficticios y comprobación del horario en evidencia.
