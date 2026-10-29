# Comparativa de dos modelos gratuitos · 29/10/2026

Prueba controlada de extracción para el entregable indicado en la [daily #26](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/26). Se consultó el [catálogo oficial de OpenRouter](https://openrouter.ai/api/v1/models) y ambos modelos declaraban precio cero de entrada/salida y soporte de respuesta estructurada. Las doce respuestas obtenidas reportaron coste cero.

## Método

Se usaron los mismos nueve correos ficticios, el mismo prompt mínimo de HU-14, esquema JSON, temperatura 0, límite de 2.000 tokens y `provider.max_price` a cero. Solo cambió el identificador del modelo. Cada modelo se llamó una vez por caso; no hubo reintentos ni sustituciones de resultados. La prueba de n8n contiene únicamente recepción ficticia, preparación de datos y llamada al modelo: no tiene nodos para consultar clientes, registrar pagos o enviar correo.

Se comparan seis campos con expectativas fijadas antes de ejecutar: clasificación, ordenante, importe, concepto, medio y número explícito de apartado. Para ordenante/concepto se admite la normalización de tildes, mayúsculas y puntuación de la validación del flujo. No se evalúa autorización de cobros, que corresponde al flujo y la API.

## Resultados

| Modelo | Respuestas correctas / intentos | Fallos HTTP 429 | Latencia media de respuestas obtenidas | Tokens totales de respuestas |
| --- | --- | --- | --- | --- |
| `dots-studio/dots-3-note-preview:free` | 9/9 | 0 | 12.67 s | 8793 |
| `liquid/lfm-2.5-2.6b:free` | 3/9 | 6 | 1.54 s | 3294 |

| Caso | Dots3-Note | LFM2.5 |
| --- | --- | --- |
| F03-01 | PASS · ejecución 538 | HTTP 429 · ejecución 547 |
| F03-02 | PASS · ejecución 539 | PASS · ejecución 548 |
| F03-03 | PASS · ejecución 540 | HTTP 429 · ejecución 549 |
| F03-04 | PASS · ejecución 541 | HTTP 429 · ejecución 550 |
| F03-05 | PASS · ejecución 542 | HTTP 429 · ejecución 551 |
| F03-06 | PASS · ejecución 543 | HTTP 429 · ejecución 552 |
| F03-07 | PASS · ejecución 544 | PASS · ejecución 553 |
| F03-08 | PASS · ejecución 545 | HTTP 429 · ejecución 554 |
| F03-09 | PASS · ejecución 546 | PASS · ejecución 555 |

En esta muestra Dots3-Note completó los nueve casos. LFM2.5 devolvió tres extracciones correctas y seis rechazos temporales por cuota/disponibilidad. Esos seis rechazos no son errores de extracción, y no permiten calcular su precisión sobre los nueve correos. La menor latencia de sus tres respuestas tampoco prueba superioridad general: la muestra es pequeña y las llamadas se hicieron en bloques, no simultáneamente.

**Decisión:** mantener `openrouter/free` y las validaciones locales de PF-03. No fijar un modelo por una única corrida. Si se necesitara fijarlo, Dots3-Note fue el más disponible en esta medición, sujeto a otra comprobación de disponibilidad. Un fallo del proveedor impide registrar el abono y exige revisión; no se cambia a un modelo de pago.

## Reproducción y trazabilidad

Ejecutar `python3 tests/n8n/comparar_modelos.py` con el laboratorio libre y la credencial nativa `PF · Modelo extracción`. Requiere Python, curl y los servicios locales; consulta el catálogo con TLS verificado y no lee ni exporta la clave del modelo. El primer intento se detuvo antes de las llamadas por el almacén de certificados de Python de macOS; se corrigió la consulta pública para usar curl y los certificados del sistema, sin desactivar TLS.

- n8n 2.44.5; ejecuciones **538–555**.
- SHA-256 de PF-03 usado: `7cd92136f2c9348865761096cdaea14a8332447cdba8fe117e1b621d027a455a`.
- Informe privado conservado: `tests/n8n/.estado/comparativa-2dd6df99d5184ce0b15e85a30363aac0.json`.
- Dieciocho intentos registrados; flujos desactivados al finalizar: **sí**.
- Esta comparación no cambia el workflow entregable ni sustituye la prueba integrada de pagos/recibos.
