# PF-04 · Aviso de venta grande

## Estado y alcance

Propuesta de nivel Medio. [HU-09 / #10](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/10). Autora: Fabiana; revisora: Rita. Entidad: Venta.

## Decisiones de implementación · 22/10/2026

SMTP local autorizado por Fabiana, reserva atómica en el registro PostgreSQL de PF-08. `UMBRAL_VENTA_GRANDE` se lee en `pf_config` en cada ejecución, sin depender de variables de pago de n8n. El JSON es un subworkflow: recibe el evento de PF-00 y no crea otro Webhook `tienda`.

Se incluye el adaptador PF-00 compartido como dependencia mínima del disparador. Sus destinos se configuran por ID real en `pf_config`; los flujos de Rita se conectan al integrarse, sin implementarlos ni editarlos aquí. Si falta un destino, la ejecución falla visiblemente. Las respuestas HTTP 200 de recepción no garantizan que el subworkflow haya terminado.

## Disparador y entradas

Evento `venta.registrada` desde PF-00: `datos.id`, `fecha`, `concepto`, `importe`, `forma_pago`. Leer `UMBRAL_VENTA_GRANDE` desde configuración externa acordada; no asumir que la edición de n8n incluye variables de pago.

## Procesamiento y salidas

Comparación estricta `importe > umbral`: enviar a Marisa el concepto, importe, fecha y medio de pago. Igual o inferior: no avisar. La variable puede cambiarse sin editar nodos. No registrar una nueva venta.

## Errores e idempotencia

Umbral ausente/no numérico: incidencia de configuración y cero avisos de venta, sin usar un valor arbitrario. Evento incompleto: PF-08. Deduplicar por `venta.registrada:<venta_id>` con persistencia del envío confirmado.

## Credenciales y variables

`PF · Notificaciones`, destinatario de Marisa, `UMBRAL_VENTA_GRANDE`, registro auxiliar. Los 100 € del contrato son una condición de prueba, no una decisión de Marisa.

## Pruebas y aceptación

[F04-01 a F04-03](../data/pruebas/contratos.json): umbral 100, importes 100,01 y 100, y variable ausente.

- [ ] Solo las ventas estrictamente superiores generan aviso.
- [ ] Cambiar la variable cambia el comportamiento sin editar el flujo.
- [ ] Una venta repetida no produce avisos duplicados; no se crean nuevas ventas.
- [ ] Datos y credenciales revisados en PR.
