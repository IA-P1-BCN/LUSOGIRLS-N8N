# Evidencia PF-07 · 22/10/2026

Laboratorio aislado de PR #32; n8n 2.44.5, SMTP local y registro PostgreSQL.

| Caso | Ejecución | Resultado observado |
| --- | --- | --- |
| F07-01 | 22; repetición 23 | Septiembre: ventas 50 €, abonos 40 €, total 90 €, pendiente actual 40 €, un nuevo, un liquidado y un vencido; sin segundo aviso |
| F07-02 | 24; repetición 25 | El 1/1/2027 consulta diciembre de 2026; listas vacías producen ceros y un solo informe |
| Fallo de vales | 26 | Tres intentos GET, ejecución fallida y cero informes completos |
| API real con semilla | 28 | Septiembre: ventas 3.868,75 €, abonos 289 €, total 4.157,75 €; pendiente actual 587,15 €, 6 nuevos, 2 liquidados y 0 vencidos |

Los contratos verifican resultados esperados independientes del código. La ejecución 28 prueba además las consultas reales de listas y detalles de la tienda aislada; sus cifras se registran como observadas. Los liquidados se cuentan por último abono, los vencidos por fecha del vale. El texto etiqueta el pendiente con el instante de consulta y «no histórico».

Las copias de prueba sustituyen el disparador y fijan el reloj; no sustituyen cálculos. JSON final importado y recuperado de n8n, inactivo y con referencias de credenciales sin ID. Programación: `0 9 1 * *`, Europe/Madrid; no se esperó al día 1. Ejecutar el test con el `lab.py` de #32 y seleccionar PF-08 al importar. Pendiente revisión de Rita.
