# Evidencia PF-09 · 27/10/2026

Laboratorio aislado (`tests/n8n/compose.yml`) con la rama al día con `dev` 8f9b8a0, n8n 2.44.5, Mailpit y PostgreSQL de pruebas. La tienda del laboratorio tiene `N8N_WEBHOOK_URL` vacío: la carga no emite eventos ni confirmaciones.

| Caso | Ejecución | Resultado |
| --- | --- | --- |
| F09-01 | 186 | Ana Torres: `2026-09-07`, precio 72, inicial 15, `forma_pago_ausente`. Cero POST con la carga permitida y autorizada |
| F09-02 | 187 | Lucía Gómez: `abono_inicial_menor_que_5`, grupo retenido entero. Cero POST |
| F09-03 | 188 | Fila `TOTAL SEPTIEMBRE (a mano)` ignorada como `total_manual`. Cero POST |
| Bloqueo sin `MIGRACION_CARGA_PERMITIDA` | 189 | Carga autorizada del lote completo: solo informe de análisis, cero POST y nada reservado en `pf_registro` |
| Carga del lote completo | 190 | 8 creadas (2 apartados y 6 ventas). Cada una comparada con la API: fecha original, importe, forma de pago y un único abono inicial por apartado |
| Segunda carga | 191 | 0 creadas, 8 ya estaban. Mismas ventas en la tienda y mismo registro |
| Abono enlazado | 192 | Con la forma de pago de Carmen: 2 creadas (apartado y abono). En la tienda, abonos de 10 € (02/09) y 20 € (05/09) y 59,90 € pendientes |

En los contratos, la API apunta al simulador, que responde 405 a cualquier POST y registra las llamadas. La carga usa la tienda aislada con semilla.

Prueba manual en la instancia de Rita (ejecución 75): informe de análisis en Mailpit con 8 operaciones listas y 6 apartados por revisar. Con `modo: carga` y `autorizada: true`, el flujo salió por la rama de informe porque esa instancia no tiene `MIGRACION_CARGA_PERMITIDA`.

PF-08 con la lista de pasos unida (83): `lab.py 08` 4/4, ejecuciones 179 a 185. Primera pasada de PF-09, antes de fusionar `dev`: 7/7, ejecuciones 172 a 178.

Reproducir: `python3 tests/n8n/lab.py`, `python3 tests/n8n/lab.py 08` y `python3 tests/n8n/lab.py 09`. El test restaura `API_BASE_URL` y `MIGRACION_CARGA_PERMITIDA` al terminar. JSON exportado de la instancia de Rita, sin ids de credenciales ni pins, e inactivo.
