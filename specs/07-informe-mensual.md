# PF-07 · Informe mensual

## Estado y alcance

Propuesta de nivel Medio. [HU-08 / #9](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/9). Autora: Fabiana; revisora: Rita. Entidades: InformeMensual, Venta, Abono, Apartado, Vale.

## Disparador y entradas

Día 1, propuesta 09:00 en `Europe/Madrid`. Fijar primer/último día del mes anterior, incluyendo cambios de año. Consultar ventas y abonos por `desde`/`hasta`; consultar todos los apartados y vales. No usar un filtro de fecha inexistente en `/api/apartados`.

## Procesamiento y salidas

- Recaudación: ventas directas y abonos del mes anterior por separado y total, en céntimos/decimal.
- Pendiente: sumar el saldo **actual al generar el informe** de apartados activos y etiquetarlo así. Un saldo histórico al cierre del mes requeriría snapshots adicionales; no presentarlo como disponible.
- Nuevos: contar `apartado.fecha` dentro del período.
- Liquidados: para cada apartado liquidado, obtener su detalle y derivar la fecha de liquidación del último abono; contar si está dentro del período. No existe `fecha_liquidacion` en la API. Incluye el inicial si ya pagó todo al crear.
- Vencidos: contar vales por su `fecha` dentro del período; no usar la fecha de creación del apartado como vencimiento.

Enviar un informe con tabla (PDF opcional) a Marisa y guardar el registro del período/envío. Un mes vacío muestra ceros.

## Errores e idempotencia

Si alguna fuente necesaria falla o no puede obtenerse completa, avisar y no declarar completo un informe parcial. Clave única del período `YYYY-MM` y destinatario para evitar envíos repetidos confirmados. Corregir un informe necesita versión y motivo explícitos.

## Credenciales y variables

API, notificaciones, registro auxiliar, horario y destino de Marisa. No se requiere un modelo de IA para las cuentas.

## Pruebas y aceptación

[F07-01 y F07-02](../data/pruebas/contratos.json): septiembre con conteos por fecha correcta y enero con período diciembre del año anterior.

- [ ] Informe del mes anterior, con ventas/abonos/total que coinciden con la API.
- [ ] Nuevos, liquidados y vencidos se cuentan con la fecha adecuada.
- [ ] Pendiente etiquetado con el momento de medición, sin inventar un histórico.
- [ ] Mes vacío, repetición y fallo de una fuente tratados de forma controlada.
