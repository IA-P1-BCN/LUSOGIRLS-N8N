# Evidencia HU-14 · 28–29/10/2026

Rama `seguridad/14-datos-personales`, sobre `dev` de la PR #36. Laboratorio n8n 2.44.5, PostgreSQL, GreenMail, Mailpit y tiendas temporales propias. Datos ficticios; sin publicación en la instancia habitual. Los archivos privados de `tests/n8n/.estado/` conservan los informes originales, incluidos los fallidos.

## Autenticación y consentimiento · 28/10

`python3 tests/n8n/test_14.py`: **16 comprobaciones PASS**, registro `qa_privacidad_3056ba36bc494c9cbc4f128fc54b3186`, tienda detenida y flujos desactivados al terminar.

| Comprobación | Ejecuciones / resultado |
| --- | --- |
| PF-00/PF-09 sin clave y con clave incorrecta | Rechazados antes de ejecutar nodos |
| PF-09 autenticado, modo análisis | 407 |
| Alta sin permiso / alta autorizada | 408–411; solo recibe el cliente autorizado |
| Abono con permiso / después de revocar | 413 / 415; tras revocar solo aviso a tienda |
| Evento atrasado que todavía dice `true` | 417; la consulta del permiso vigente evita el envío al cliente |
| API de consentimiento inaccesible | 421; falla cerrado y activa PF-08 |
| Preparación de recordatorios y vales | 424–431; altas con/sin permiso diferenciadas |
| PF-06 con/sin permiso y repetición | 432 / 437; dos vales, cinco avisos y ningún duplicado |

## Extracción mínima con OpenRouter real · 29/10

El registro `qa_recibos_e3b68be9a6d5472c98cd6342ce99c6a1` conserva **nueve casos PASS** con la nueva petición mínima de PF-03, sin cambiar las expectativas ni los correos originales.

| Caso | IMAP / PF-03 | PF-00 / PF-02 | Efecto comprobado |
| --- | --- | --- | --- |
| F03-01 | 446 / 447 | 448 / 449 | Un abono y un recibo |
| F03-02 | 450 / 451 | 452 / 453 | Un abono y un recibo |
| F03-03 | 454 / 455 | 456 / 457 | Transferencia que liquida; recibo de recogida |
| F03-04 | 458 / 459 | — | Exceso: revisión, ningún abono |
| F03-05 | 460 / 461 | — | Identidad insuficiente: revisión, ningún abono |
| F03-06 | 462 / 463 | — | Fuera de plazo: revisión, ningún abono |
| F03-07 | 464 / 465 | — | Desconocido: revisión, ningún abono |
| F03-08 | 466 / 467 | — | Publicidad: ningún abono ni correo |
| F03-09 | 468 / 469 | 470 / 471 | Un abono y un recibo |

El test original terminó **FAIL** por HTTP 503 del laboratorio al repetir, con limpieza incompleta; no se ha cambiado ese resultado. Su ejecución IMAP 472 quedó en error. Los intentos anteriores del 28/10 y 29/10 tampoco se cuentan como éxitos.

Después de recuperar el laboratorio se conciliaron por API los abonos, el buzón y las ejecuciones. Se reactivaron únicamente las cuatro copias de esa corrida y se repitió el mismo Message-ID sobre **la misma base**, conservando sus reservas: **IMAP 474 / PF-03 475, PASS**, cero abonos, cero recibos y ninguna nueva ejecución de PF-02. Se comprobó que PF-03 llegó a `Reservar correo` y no consultó apartados. Informe separado: `repeticion-recuperada.json`. Los cuatro flujos quedaron desactivados y la tienda de prueba detenida. Son nueve casos más una comprobación recuperada, no una corrida única de diez casos terminada con código cero.

Se observaron modelos gratuitos del enrutador, incluido `dots-studio/dots-3-note-preview:free`. Se conserva `openrouter/free` con precio máximo cero; esta corrida no sustituye una comparación controlada de dos modelos. Solo se envía la petición descrita en [datos personales](../datos-personales.md).

## Retención y exportación · 29/10

`python3 tests/n8n/test_14_exportacion.py`: **PASS**. PF-00 (`VIacyg5zO5Rulyon`) y PF-09 (`f0h3neHyExhZyurL`) procesaron entradas ficticias autenticadas y produjeron el aviso esperado en Mailpit; sus historiales quedaron vacíos. También se comprobó el error de PF-00 con historial vacío y aviso de PF-08. No se puede adjuntar un ID de ejecución persistido de un webhook cuyo historial se ha desactivado: se conservan IDs de workflow y la observación del efecto.

Se importaron y exportaron inactivos PF-00, PF-01, PF-02, PF-03, PF-06, PF-08 y PF-09, verificando nodos, conexiones y settings, sin datos fijados ni IDs locales de credenciales. Registro privado `14-retencion-exportacion.json`. Al importar, SMTP puede incorporar `webhookId` de metadatos; no se alteran sus parámetros ni lógica.

## Comprobaciones locales · 29/10

- Backend completo: **20/20 PASS**, contenedor temporal sin red y base de pruebas propia.
- `node --test tests/n8n/test_14_code.cjs`: **6/6 PASS**, permiso explícito, revocación, minimización, rechazo de formatos y referencias de credenciales.
- `python3 tests/n8n/test_credenciales.py`: **3/3 PASS**.
- JSON, sintaxis de nodos Code, enlaces y `git diff --check` se verifican antes de entregar la PR.

Pendientes revisión humana e integración. El acceso público de la app, HTTPS y las copias de seguridad pertenecen a HU-16; estas pruebas no acreditan esos requisitos ni cumplimiento legal integral.
