# PF-09 · Migración del Excel antiguo

## Estado y alcance

Propuesta de nivel Medio. [HU-10 / #11](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/11). Autora: Rita; revisora: Fabiana. Entidades: Cliente/Producto conceptuales, Apartado, Abono, Venta y registro auxiliar de migración.

## Disparador y entradas

Manual, primero en modo análisis sin escrituras. Archivos [apartados](../data/excel_actual_apartados.csv) y [ventas](../data/excel_actual_ventas.csv). Mantener copia de origen y referencia estable a cada fila. No tratar la columna `resta` calculada a mano como saldo de la API.

## Procesamiento y salidas

Normalizar fechas y decimales con reglas explícitas (día/mes/año; `7/9/26` pertenece a 2026 en este conjunto), quitar `€` y espacios, y reconciliar nombres sin mezclar clientes distintos. Relacionar filas de abono con el apartado correcto usando contexto, producto, talla y contacto; casos ambiguos a informe humano.

Crear apartados, abonos y ventas por API conservando `fecha`. El primer abono no se registra dos veces: ya lo crea `POST /api/apartados`. Ignorar filas de totales manuales y separar las filas de ventas que describen abonos para no duplicar cobros.

Los apartados con inicial inferior a 5 € quedan pendientes de Marisa, incluyendo el resto de filas del mismo grupo. Si falta la forma de pago, no aceptar silenciosamente `efectivo` por ser el valor por defecto: acordar una regla o dejar la fila para revisión. No cambiar las fechas para evitar las reglas de plazo.

## Errores e idempotencia

Mantener una clave persistente por archivo/fila normalizada, relación con el registro creado y estado de operación. Segunda ejecución: saltar registros confirmados. Ante timeout de un POST, conciliar y pedir revisión si no hay certeza; no repetir toda la carga. Las filas inválidas no impiden producir el informe de incidencias del lote.

La carga emite webhooks. Usar una instancia de pruebas o una estrategia explícita de bloqueo de notificaciones durante migración antes de escribir; no mandar confirmaciones de registros históricos a clientes reales.

## Credenciales y variables

API, registro auxiliar de migración, modo `analisis`/`carga` y política de notificaciones acordada. La carga necesita una decisión humana tras revisar el informe de análisis.

## Pruebas y aceptación

[F09-01 a F09-03](../data/pruebas/contratos.json): normalización de Ana, inicial inválido de Lucía y fila de total. Ejecutar también el lote completo dos veces en un entorno aislado.

- [x] Fechas e importes normalizados de forma reproducible.
- [x] Las fechas originales llegan a la API; no se duplican iniciales ni abonos presentes en ambos CSV.
- [x] Iniciales menores de 5 €, identidad dudosa y medio ausente aparecen en el informe para Marisa.
- [x] Segunda ejecución no crea registros nuevos ya confirmados.
- [ ] Evidencia del análisis, autorización de carga y resultados adjunta a la PR.

## Decisiones de implementación · 27/10/2026

Decididas por Rita al construir el flujo. Evidencia en [docs/pruebas/09-migracion.md](../docs/pruebas/09-migracion.md).

- Entrada: Webhook manual `POST /webhook/migracion` con `modo`, `autorizada`, `csv_apartados` y `csv_ventas` (texto de los dos CSV). El contenedor de n8n no monta `data/`. Sin `modo: carga`, el modo es `analisis`.
- Normalización: fechas día/mes/año (año de dos cifras = 2000 + aa); importes a céntimos enteros sin `parseFloat`, con formato español explícito (`1.842,30`). Un importe ambiguo como `1.842` se marca inválido. Nombres comparados sin tildes ni mayúsculas.
- Agrupación: un apartado es el mismo cliente, producto y talla. La fila más antigua es el inicial y las demás, abonos. Se retiene el grupo entero si hay inicial menor de 5 €, identidad dudosa (mismo nombre con teléfonos distintos o un teléfono con nombres distintos), precio inconsistente, pagos por encima del precio o abono fuera de los 90 días. Un cliente sin teléfono se enlaza por nombre, producto y talla, con aviso en el informe. La regla de identidad dudosa no tiene caso en el lote actual.
- Forma de pago: no se usa el `efectivo` por defecto. Solo se toma del CSV de ventas cuando una única fila coincide en fecha, importe y cliente o producto; esa fila deja de contar como venta. Un grupo solo pasa a la carga si todos sus pagos tienen forma de pago. Con los datos actuales: 2 apartados listos, 5 en revisión por forma de pago, 1 retenido (Lucía), 6 ventas reales, 3 pagos de apartados en el libro de ventas y 1 total manual ignorado.
- Informe: correo a Marisa (`CORREO_MARISA`) con incidencias y plan de carga. Se envía sin reserva en `pf_registro` porque no cambia datos.
- Bloqueo de notificaciones (opción 1A): la carga solo se ejecuta con `modo: carga`, `autorizada: true` y `MIGRACION_CARGA_PERMITIDA = si` en `pf_config`. Esa clave solo existe en el laboratorio, cuya tienda no emite webhooks. En otra instancia, una carga autorizada produce el informe de análisis.
- Idempotencia: clave `migracion:<archivo>:<fila>` reservada en `pf_registro` antes de cada POST. Las operaciones se recorren de una en una; un abono solo se reserva cuando su apartado está `confirmado` y toma su id. Una clave existente se salta sin llamar a la API.
- Fallos (opción 2A): POST sin reintentos. Un error o timeout deja la clave en `revision` con la respuesta; una caída entre el POST y la confirmación la deja en `reservado`. El correo de resultado lista ambos casos para conciliar a mano.
- Mejora pendiente (opción 2B): conciliación automática tras un timeout, buscando la operación en la API. Se descartó por calendario y porque emparejar por cliente, fecha e importe puede confundir operaciones iguales.
