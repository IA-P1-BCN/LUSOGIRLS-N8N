# Evidencia PF-08 · 22/10/2026

Instancia aislada: n8n 2.44.5, PostgreSQL 16, Mailpit 1.27, proyecto Docker `lusogirls-pruebas`. Datos ficticios. Ejecuciones conservadas en el volumen del laboratorio, no en la instancia personal de Fabiana.

| Caso | Ejecución n8n | Resultado observado |
| --- | --- | --- |
| Error automático real | Emisor 8; PF-08 9 | Un correo con flujo, paso y resumen seguro; sin el mensaje sensible original |
| F08-01 | 10; repetición 11 | Un correo; clasificación de HTTP 401; sin Authorization ni credencial ficticia; repetición sin nuevo envío |
| F08-02 | 12; repetición 13 | Paso y ejecución «no disponible»; sin inventar ID; repetición sin nuevo envío |
| SMTP inaccesible | 14 | Ejecución fallida visible, reserva conservada, cero correos y sin recursión |

Comando: `python3 tests/n8n/lab.py 08`, después de preparar el laboratorio. El JSON se recuperó de n8n después de importarlo y ejecutar las pruebas. Se eliminaron IDs de credenciales de esta instancia y se dejó `active: false`; los nombres de credenciales se conservan.

Incidencias encontradas y corregidas: esperar el registro del webhook tras publicar la copia de prueba; publicar también el Error Workflow en esta versión; el nodo Postgres puede devolver un item `success` cuando `RETURNING` no devuelve filas, por lo que se añadió una comprobación explícita de reserva antes de SMTP.

La prueba automática usa una copia de emisor creada exclusivamente para fallar. Para los contratos de formato, se sustituye únicamente el disparador por un Webhook de laboratorio. Al acabar se desactivan todas esas copias. No se publicó ningún flujo de la instancia habitual ni se enviaron correos externos.

Pendiente de revisión: Rita importa y repite pruebas. Los flujos de negocio de ambas integrantes deben seleccionar PF-08 en Settings → Error Workflow cuando se integren; sus IDs son propios de cada instancia. No se atribuye esa configuración a flujos de Rita que aún no existen en el repositorio.
