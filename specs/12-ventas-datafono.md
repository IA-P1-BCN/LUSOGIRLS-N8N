# PF-12 · Ventas del datáfono (HU-13)

Responsable: Fabiana; revisora: Rita. Fabiana eligió importar el CSV nocturno el 28/10/2026. La alternativa de apartados por Telegram/formulario queda fuera de esta entrega. PF-10/HU-11 y HU-12 pertenecen a Rita; este flujo no modifica sus bots ni PF-00.

## Entrada y disparador

Schedule Trigger a las 00:01 en `Europe/Madrid`, antes del cierre PF-05 propuesto a las 00:05. Manual Trigger para una repetición controlada. Ambos procesan el día anterior completo. No se activa en producción como parte del desarrollo.

HTTP GET de `DATAFONO_CSV_URL`, sustituyendo `{fecha}` por `YYYY-MM-DD` del día anterior. Credencial Header Auth independiente `PF · Fuente datáfono`; sin claves en URL ni nodos. La URL y los destinatarios se configuran en `pf_config`. Sin fuente/configuración válida, fallar y avisar mediante PF-08. Redirecciones desactivadas para no reenviar la cabecera a otro servidor. La descarga puede reintentarse de forma acotada; nunca un POST de venta.

Formato de intercambio definido para este flujo (el exportador del datáfono debe adaptarse; no se afirma compatibilidad con un banco no probado): UTF-8, separador `;`, cabecera exacta:

```csv
terminal_id;operacion_id;fecha;tipo;concepto;importe;moneda;venta_id
TPV01;TX001;2026-10-27;venta;Zapatos negros;39,90;EUR;
```

`terminal_id` y `operacion_id`: referencias estables, 1–64 caracteres alfanuméricos, `_` o `-`; únicas conjuntamente, independientes del nombre/posición del archivo. `fecha`: ISO y exactamente el día procesado. Solo `tipo=venta`, `moneda=EUR`, importe positivo con coma o punto decimal y hasta dos decimales, sin miles. Un máximo de 2.000 filas y 1 MiB. Comillas dobles y separadores dentro de un campo se procesan como CSV; cabecera incorrecta o estructura rota rechazan el lote entero antes de escribir.

No importar abonos de apartados, devoluciones ni totales como ventas. Las filas inválidas aparecen en el informe y no se escriben. Una referencia repetida con contenido distinto bloquea todas sus filas; si es idéntica se procesa una sola vez.

## Duplicados y ventas ya registradas

Entidad nueva conceptual: `CobroDatafono` (terminal, operación, fecha, importe en céntimos, concepto, vínculo opcional a Venta). La app conserva su API actual: no se inventa un campo `referencia_externa` ni un endpoint de datáfono.

1. Consultar por API todas las ventas del día. `venta_id`, cuando existe, identifica una venta ya registrada: deben coincidir fecha, tarjeta e importe; también el concepto normalizado o la referencia del datáfono. No volver a crearla.
2. Las nuevas ventas se registran con concepto `[TPV:<terminal>:<operacion>] <concepto>`. La referencia permite reconocerlas también tras perder el registro auxiliar. Una referencia existente con importe/fecha incompatible pasa a revisión.
3. Una venta previa con tarjeta del mismo importe/día y sin referencia de datáfono puede ser la misma operación. Se retiene para revisión, sin deducir identidad solo por el importe. Marisa puede aportar `venta_id` en el CSV y volver a ejecutarlo. Dos operaciones nuevas con IDs distintos, mismo importe y día siguen siendo dos ventas legítimas.
4. Reservar atómicamente `datafono:<terminal>:<operacion>` en PostgreSQL antes del POST. La clave no incluye fecha ni número de fila. Conservar el documento normalizado: la misma referencia con contenido cambiado se informa como conflicto y nunca provoca otro POST.
5. POST `/api/ventas` una sola vez, con fecha del cobro y `forma_pago=tarjeta`. Confirmar solo si la respuesta coincide con el documento enviado y contiene ID válido. Error/timeout deja `revision`; caída posterior al POST deja `reservado`. Las siguientes ejecuciones concilian por la referencia de la API; sin una coincidencia inequívoca no repiten la escritura. No prometemos entrega exactamente una vez.

Las retenciones detectadas antes de reservar no crean una marca irreversible: pueden resolverse corrigiendo el CSV. Las operaciones enviadas o con resultado incierto nunca se desbloquean automáticamente para un nuevo POST.

## Salidas y errores

Informe a `CORREO_MARISA`: fecha, ventas nuevas, ya existentes, duplicados del archivo y filas/conflictos por revisar. Sin números de tarjeta, titulares ni datos bancarios; el CSV de intercambio tampoco debe contenerlos. SMTP usa `PF · Notificaciones`.

Errores técnicos del flujo se asocian a PF-08. El informe registra incidencias de negocio sin copiar respuestas HTTP completas ni cabeceras. El fallo del correo no revierte ventas confirmadas; al repetir no se duplican. No recalcular automáticamente cierres ya confirmados: una descarga fallida o corrección tardía requiere revisar el cierre de ese día.

## Credenciales y configuración

- `PF · Registro auxiliar`: PostgreSQL para `pf_config` y `pf_registro`.
- `PF · API tienda`: Header Auth `X-API-Key`.
- `PF · Fuente datáfono`: Header Auth del servicio que expone el CSV.
- `PF · Notificaciones`: SMTP.
- `API_BASE_URL`, `DATAFONO_CSV_URL`, `CORREO_MARISA`, `CORREO_REMITENTE`: valores no secretos en `pf_config`.

## Aceptación y prueba

- CSV real descargado desde un servicio local de prueba → n8n → API real de una tienda aislada → correo local; dos ventas nuevas con misma fecha/importe e IDs diferentes se crean separadamente.
- Repetir o reordenar el mismo CSV no crea otra venta. Referencia cambiada, fila inválida, tipo abono/devolución y moneda distinta quedan sin escritura.
- Venta ya registrada con `venta_id` válido o marcador se reconoce; coincidencia ambigua sin referencia se retiene.
- Cabecera/CSV roto rechaza todo el lote. Vacío con solo cabecera produce informe de cero ventas.
- Conflicto con una clave confirmada se informa sin alterar su documento original.
- Simular resultado incierto y repetir: conciliar por API o mantener revisión; nunca repetir a ciegas el POST.
- Comprobar reserva concurrente; importar/exportar el JSON final sin IDs de credenciales, guardar IDs reales de ejecución y solicitar revisión de Rita.
