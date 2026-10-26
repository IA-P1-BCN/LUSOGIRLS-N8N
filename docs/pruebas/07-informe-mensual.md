# Evidencia PF-07 · 26/10/2026

Laboratorio aislado `lusogirls-pruebas`; n8n 2.44.5, SMTP Mailpit y registro PostgreSQL. Rama actualizada con `dev` (`6311a27`), incluido el PF-08 corregido. Esta corrida sustituye la evidencia del 22/10 y responde a la revisión de Rita en la PR #34.

| Caso | Ejecución | Resultado observado |
| --- | --- | --- |
| F07-01 | 117; repetición 118 | Septiembre: ventas 50 €, abonos 40 €, total 90 €, pendiente actual 40 €, un nuevo, un liquidado y un vencido; un aviso, estado `confirmado` y ningún segundo aviso |
| F07-02 | 119; repetición 120 | El 1/1/2027 consulta diciembre de 2026; listas vacías producen ceros, un solo informe y estado `confirmado` |
| Fallo de vales | 121 | Tres intentos GET, ejecución fallida y cero informes completos |
| API real con semilla | 123 | Período 1–30/9/2026: API e informe coinciden en ventas 386.875 céntimos, abonos 28.900 céntimos y total 415.775 céntimos; estado `confirmado` |

## Comprobaciones independientes

- Para F07-01 y F07-02 se exige que existan consultas a **ventas y abonos** y que todas lleven exactamente los parámetros `desde` y `hasta` del contrato. Apartados y vales se consultan sin filtros inexistentes.
- Después del primer envío se comprueba un único correo y que `pf_registro.estado` sea `confirmado`. La repetición conserva una sola fila y no genera otro correo.
- Para la API real, Python calcula el mes anterior con `Europe/Madrid`, consulta por separado `GET /api/ventas` y `GET /api/abonos` en `http://127.0.0.1:18000` y suma los importes con `Decimal` en céntimos. Las tres aserciones comparan ventas, abonos y total con el documento persistido del workflow; el cálculo esperado no reutiliza el código ni los totales del flujo. También se verifica el período y el estado `confirmado`.
- Los contratos comprueban conteos por fecha: liquidados por último abono y vencidos por fecha del vale. El pendiente se etiqueta como actual, con el instante de consulta y «no histórico»; en la API semilla se observaron 587,15 €, 6 nuevos, 2 liquidados y 0 vencidos.

Las copias de prueba sustituyen el disparador y fijan el reloj; no sustituyen cálculos. JSON final importado y recuperado de n8n, inactivo y con referencias de credenciales sin ID. Programación: `0 9 1 * *`, Europe/Madrid; no se esperó al día 1.

Reproducción: preparar [el laboratorio](../automatizaciones-locales.md), instalar el PF-08 actual y ejecutar `python3 tests/n8n/lab.py 07` desde la rama de PF-07. La ejecución de esta corrida utilizó el `lab.py` del clon principal y la ruta absoluta de `test_07.py` del worktree, compartiendo únicamente la instancia aislada y su configuración local. La evidencia JSON sin secretos queda en `tests/n8n/.estado/07-evidencia.json`, ignorada por Git. Pendiente nueva revisión de Rita; no se publicó en la instancia habitual.
