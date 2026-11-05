# Evidencia PF-05 · 22/10/2026

Laboratorio de [PR #32](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/pull/32), n8n 2.44.5, SMTP Mailpit y PostgreSQL separados de la tienda habitual.

| Caso | Ejecución | Resultado |
| --- | --- | --- |
| F05-01 | 15; repetición 16 | Ventas 50,00 €, abonos 15,30 €, total 65,30 €; efectivo 25,00 €, tarjeta 30,30 €, Bizum 10,00 €. Una fila y ningún envío repetido |
| F05-02 | 17; repetición 18 | Ceros y «Sin movimientos»; una fila y un aviso |
| F05-03 | 19 | Tres GET fallidos de abonos; ningún cierre parcial guardado; error asociado a PF-08 |
| API real con semilla | 21 | Ventas 184,00 €, abonos 89,90 €, comparados con consultas HTTP independientes y Decimal |

Los contratos usan un doble HTTP que conserva la forma y cabeceras de la API; solo se cambia el disparador por un Webhook de pruebas y se fija el reloj. No se cambian las sumas ni los resultados esperados. El cuarto caso consulta la API real aislada. Programación exportada: `5 0 * * *`, Europe/Madrid; cierre del día anterior. No se esperó a medianoche ni se publicó en la instancia habitual.

Reproducir, con la infraestructura de #32 disponible: `python3 tests/n8n/lab.py /ruta/al/checkout/tests/n8n/test_05.py`. JSON importado y recuperado de n8n; IDs de credenciales retirados y archivo inactivo. Revisar primero #32, seleccionar sus credenciales y PF-08 en cada instancia. Una reserva incierta tras SMTP requiere conciliación manual.
