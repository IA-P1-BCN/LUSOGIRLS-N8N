# HU-13 · Importar las ventas del datáfono

Fabiana eligió **CSV nocturno** el 28/10, una de las dos alternativas de HU-13. Telegram para consulta de saldos y del negocio sigue en las tareas de Rita; PF-12 no modifica esos flujos.

Cada noche a las 00:01 (`Europe/Madrid`), PF-12 descarga el CSV del día anterior, consulta las ventas de ese día por API, importa ventas directas con tarjeta y envía un informe a Marisa. Una ejecución manual vuelve a comprobar el día anterior; no borra reservas ni fuerza operaciones pendientes.

## Configurar una instancia

1. Leer la [spec](../specs/12-ventas-datafono.md). La fuente debe entregar el formato acordado: no se ha conectado un banco o terminal real.
2. Aplicar [registro.sql](../infra/registro.sql) y [12-datafono.sql](../infra/12-datafono.sql) en PostgreSQL auxiliar. Nunca ejecutarlos contra SQLite de la tienda.
3. Importar [PF-12](../workflows/12-ventas-datafono.json) y la exportación actualizada de [PF-08](../workflows/08-errores.json), sin publicar. Elegir PF-08 como Error Workflow de PF-12 en la instancia.
4. Seleccionar las cuatro credenciales y configurar `pf_config` según las tablas. Probar con datos ficticios, revisar con Rita y obtener autorización expresa antes de publicar.

| Credencial | Configuración privada |
| --- | --- |
| `PF · Fuente datáfono` | Header Auth del servicio que entrega el CSV; sin claves en URL |
| `PF · API tienda` | Header Auth `X-API-Key` de la tienda, independiente de la fuente CSV |
| `PF · Registro auxiliar` | PostgreSQL de automatizaciones |
| `PF · Notificaciones` | SMTP; Mailpit para las pruebas |

| Clave en `pf_config` | Valor no secreto |
| --- | --- |
| `DATAFONO_CSV_URL` | URL HTTP(S); `{fecha}` se sustituye por el día anterior ISO. Ejemplo conceptual: `https://exportador.example/cobros-{fecha}.csv` |
| `API_BASE_URL` | Dirección interna de la tienda, sin `/api` final |
| `CORREO_MARISA` | Destino autorizado del informe |
| `CORREO_REMITENTE` | Remitente SMTP |

No se siguen redirecciones ni se toman URLs del CSV. La fuente debe entregar el archivo completo antes de las 00:01. PF-05 cierra a las 00:05: una importación fallida, lenta o corregida después requiere revisar el cierre; no se reescribe automáticamente un cierre confirmado.

## CSV y referencias

UTF-8, separador `;`, cabecera exacta incluso sin ventas:

```csv
terminal_id;operacion_id;fecha;tipo;concepto;importe;moneda;venta_id
TPV01;TX001;2026-10-27;venta;Zapatos negros;39,90;EUR;
TPV01;TX002;2026-10-27;venta;Sandalias;25,00;EUR;123
```

Sustituir las fechas por el día procesado. `123` solo ejemplifica una venta ya registrada; no aportar un vínculo sin verificarlo. No incluir tarjetas, titulares, correos, teléfonos ni otros campos bancarios. No se llama a IA.

La referencia estable es `terminal_id + operacion_id`, independiente del orden de filas y nombre del archivo. Dos cobros con IDs distintos e importe igual se conservan. Se valida el dinero en céntimos.

Como la API no tiene un campo de referencia externa, las nuevas ventas usan el concepto `[TPV:terminal:operacion] concepto`. Una venta ya registrada puede indicarse mediante `venta_id`, con fecha, importe, tarjeta y concepto compatibles. Una posible venta manual sin vínculo fiable se retiene. El índice auxiliar impide asociar dos referencias a la misma venta.

Abonos de apartados, devoluciones, moneda distinta, fechas ajenas al día, referencias incompatibles e importes inválidos aparecen como incidencias, sin escritura. Una estructura/cabecera rota rechaza todo el lote. Máximo 2.000 filas y 1 MiB.

## Ante un fallo

Un POST de venta no se repite automáticamente. La respuesta puede perderse después de crear la venta. La reserva persiste en `revision`/`reservado`; otra ejecución consulta la API y solo confirma una referencia inequívoca. Sin coincidencia mantiene la incidencia. No borrar la reserva para «probar de nuevo».

Un fallo SMTP no revierte ventas. Repetir permite recibir otro informe sin crear otra venta. PF-08 identifica flujo/paso con una lista permitida y omite mensajes HTTP completos, cuerpos y cabeceras.

## Prueba local

Preparar el [laboratorio](automatizaciones-locales.md) y comprobar que esté libre. El test crea una base auxiliar, volumen y contenedores propios; usa `28000` para su tienda y conserva evidencias. Al acabar apaga únicamente sus recursos, sin cambiar la tienda compartida.

```bash
node --test tests/n8n/test_12_code.cjs
python3 tests/n8n/test_12.py
```

Incluye CSV HTTP autenticado, API real, Mailpit, repeticiones, venta manual, datos inválidos, respuesta perdida, ejecuciones concurrentes y Schedule Trigger real con cadencia de un minuto en una copia. El JSON entregable conserva las 00:01 y se exporta inactivo. Ver [resultados observados](pruebas/12-ventas-datafono.md).
