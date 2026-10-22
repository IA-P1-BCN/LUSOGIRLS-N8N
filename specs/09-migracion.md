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

- [ ] Fechas e importes normalizados de forma reproducible.
- [ ] Las fechas originales llegan a la API; no se duplican iniciales ni abonos presentes en ambos CSV.
- [ ] Iniciales menores de 5 €, identidad dudosa y medio ausente aparecen en el informe para Marisa.
- [ ] Segunda ejecución no crea registros nuevos ya confirmados.
- [ ] Evidencia del análisis, autorización de carga y resultados adjunta a la PR.
