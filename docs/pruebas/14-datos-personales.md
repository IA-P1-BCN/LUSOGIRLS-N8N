# Evidencia HU-14 · 28–29/10/2026

Rama `seguridad/14-datos-personales`, integrada con `dev` `b416e2a` (incluida la PR #43) mediante `d6ee6a1`. Laboratorio n8n 2.44.5, PostgreSQL, GreenMail, Mailpit y tiendas temporales propias. Datos ficticios; sin publicación en la instancia habitual. Los archivos privados de `tests/n8n/.estado/` conservan los informes originales, incluidos los fallidos.

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

## Repetición sobre dev actualizado · 29/10

Tras integrar PF-10 de Rita se conservaron en PF-08 los nombres de flujo y pasos de ambas ramas. La suite completa de HU-14 volvió a pasar: **16/16**, registro `qa_privacidad_0c30c3864ba84fd7a9ab201499049470`, ejecuciones **481–511**. Alta sin/con permiso: 482–485; recibo con permiso: 487; revocación: 489; evento atrasado: 491; fallo cerrado de la consulta: 495; recordatorios/vales: 506 y repetición 511. La tienda compartida se preservó; la tienda temporal quedó detenida y las copias desactivadas.

Después del merge también pasaron 6/6 tests de código, 3/3 de credenciales y la validación estática de los once workflows. Los 47 archivos de la entrega se comprobaron contra los secretos locales sin imprimirlos; no hubo coincidencias ni enlaces locales rotos.

La retención/exportación volvió a pasar después de esa corrida sobre `dev` actualizado. PF-00 `mDzBFOqP4ov0m55C` y PF-09 `8wYAEwhdj2di4b1o` no conservaron historial; las siete exportaciones inactivas se verificaron de nuevo. PF-08 final: `Ip77K2SCpM7MlMdE`, SHA-256 `66b5614af3f62761c7ca1833e4a58fa06763db644bc74d2b62e3783d60750699`.

Se completó además la [comparación controlada de dos modelos gratuitos](../comparativa-modelos-gratuitos.md), ejecuciones 538–555. Dots3-Note: nueve respuestas correctas. LFM2.5: tres respuestas correctas y seis rechazos HTTP 429; estos últimos no se presentan como errores de extracción. No se modificó el modelo del workflow entregable.

## Regresión de cierre, informe y errores · 29/10

Las suites existentes se ejecutaron con el adaptador local de revisión que asigna una base PostgreSQL, tienda y credencial SMTP propias a cada prueba. Conserva las expectativas y contrasta por API los totales reales; no recrea la tienda compartida.

| Flujo | Ejecuciones | Resultado |
| --- | --- | --- |
| PF-08 | 512–518 | Error Trigger real, dos contratos con repeticiones y SMTP fallido sin recursión: PASS |
| PF-05 | 519–525 | Cierre normal, sin movimientos, fuente fallida y API real: PASS. API real: ventas 184,00 €, abonos 89,90 € |
| PF-07 | 526–532 | Mes normal, cambio de año sin movimientos, fuente fallida y API real: PASS. API real: ventas 4.128,30 €, abonos 199,50 €, total 4.327,80 € |

Registros conservados: `qa_review_3bb840919fe54886bd364da0161b6556`, `qa_review_c4577e89a91c41d9bc9967ee11b71ae9` y `qa_review_c846e6c6e03b4501a46c602b405ba665`. Limpieza verificada en los tres; las exportaciones resultantes de PF-05/PF-07/PF-08 son idénticas a las anteriores al test. No se esperó a las horas de los calendarios: las copias usan disparadores y reloj de prueba.

## Correcciones solicitadas por Rita en #45 · 29/10

Versión: `1db4e4e` más `dev` `af43d74` (incluida #42), con el conflicto de PF-08 resuelto conservando los doce nombres de flujo y la unión de 113 pasos permitidos. PF-10 y PF-12 se mantienen. El resto del código de `Preparar aviso` coincide con ambas ramas.

Rita identificó un 404 en la tercera parte de `test_06.py`: la conciliación sustituía el fixture y dejaba de existir el permiso del apartado 9004. Antes de invocar el evento se carga explícitamente su consentimiento ficticio. Se conservan las expectativas, la comprobación de cero avisos duplicados y la lógica del workflow PF-06.

Se ejecuta completo `tests/n8n/test_06.py` (la suite invocada por `python3 tests/n8n/lab.py 06`) mediante el adaptador local de aislamiento, asignándole base PostgreSQL, tienda con `SEED=1`, simulador y credenciales de prueba propios. Se conserva Mailpit local y el webhook de la tienda de prueba está vacío. **7/7 PASS; proceso terminado con código 0**, incluida la cuarta parte contra la API real.

| Caso | Ejecución | Resultado observado |
| --- | --- | --- |
| F06-01, recordatorio de siete días | 573 | Un correo; ningún POST de vencimiento |
| F06-02, aviso ya confirmado | 574 | Cero correos y cero POST |
| F06-03, fecha límite hoy | 575 | Cero correos y cero POST |
| F06-04, vencimiento y vale | 576 | Un POST al simulador; dos avisos con el vale del fixture |
| Conciliación y correo ausente | 577 | Un aviso a Marisa; vale antiguo fuera de ventana |
| Evento después del calendario | 578 | Consulta de consentimiento correcta; cero correos duplicados |
| API real con semilla | 579 | Tres apartados vencidos con sus vales y siete avisos nuevos; estados, importes y claves contrastados por API |

PF-08 se importa y recupera de n8n sin diferencias con el JSON corregido. Las doce exportaciones pasan el validador estático; los contratos JSON y la sintaxis del test son válidos. La tienda compartida conserva ID, montajes y estado. La tienda/simulador propios quedan detenidos y no quedan workflows activos en el laboratorio. Informes conservados en `tests/n8n/.estado/qa_review_d6ebf969f1364dc8870468b4a1136bd0/06-evidencia.json` y `limpieza.json` (ignorados por Git).

No se repiten las suites que Rita ya verificó ni se llama a OpenRouter. La observación opcional sobre reintentos ante 401 queda fuera de esta corrección. Sigue pendiente la nueva aprobación humana de Rita.
