# Datos ficticios de demo por API

El [script](../scripts/preparar_demo_api.py) cubre el pendiente de la daily #26: prepara un apartado activo, otro liquidado, otro vencido con vale y una venta directa, usando exclusivamente la API. No llama a SQLite ni usa `backend/seed.py`.

## Preparación y contrato

- **Entrada:** URL HTTP local de pruebas y `PF_DEMO_API_KEY` en el entorno. Configurar una tienda aislada con `SEED=0` y `N8N_WEBHOOK_URL` vacío para preparar ejemplos sin notificaciones. La clave no se pasa como argumento ni se imprime.
- **Ejecución:** `python3 scripts/preparar_demo_api.py --url http://127.0.0.1:28001`. Solo se admiten direcciones de loopback; no hay redirecciones HTTP.
- **Salida:** `tests/n8n/.estado/demo-presentacion.json`, ignorado por Git, con IDs, respuestas y estado de cada operación. Si el archivo existe, se rechaza una nueva carga.
- **Errores:** antes de cada POST se conserva el intento. Si la respuesta es incierta, se detiene y requiere conciliar por API; no hay reintentos ni borrado de registros.
- **Aceptación:** consultar los apartados por API y comprobar los estados, saldos de la app, plazo de 90 días y vale de 20 €. El script realiza estas comprobaciones al terminar. Cambiar permisos o registrar nuevos abonos queda fuera de esta carga.

| Ejemplo | Precio / abonado / pendiente | Resultado |
| --- | --- | --- |
| Activo | 60 / 20 / 40 € | Listo para enseñar un abono final de 40 € en un ensayo posterior |
| Liquidado | 40 / 40 / 0 € | Alta con 10 €, después abono de 30 € |
| Vencido | 80 / 20 / 60 € | Fecha de hace 91 días, vencido por API y vale de 20 € |
| Venta directa | 25 € | Venta por efectivo, separada de los abonos |

Los destinatarios son ficticios `example.test` y no se atribuye consentimiento. Esta preparación prueba la API y sus datos; la demo completa de notificaciones requiere una copia de n8n configurada con Mailpit, destinatarios ficticios y permiso explícito cuando se use HU-14.

## Resultado observado · 29/10/2026

Carga ejecutada en `lusogirls-demo-20261029`, puerto [28001](http://localhost:28001), con volumen propio, `SEED=0`, backend de la rama HU-14 y webhook deshabilitado. Apartados **1, 2 y 3**, venta **1**, vale **VALE-00003** de **20,00 €**. Los tres estados, saldos y fechas se contrastaron por GET. Una segunda ejecución del script fue rechazada por el registro existente antes de enviar operaciones. No se modificó la tienda compartida ni se generaron correos de esta carga.
