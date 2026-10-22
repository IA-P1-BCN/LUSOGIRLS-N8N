# Evidencia PF-03 · 22/10/2026

**Validación parcial: API y reglas reales con IA simulada.** OpenRouter real, recepción IMAP y recibo PF-02 pendientes. HU-03 permanece en progreso y la PR se abre en borrador.

Entorno: n8n 2.44.5, PostgreSQL, Mailpit y app en el proyecto Docker aislado `lusogirls-pruebas`. Cada corrida crea otra base semilla, con fechas relativas al día de creación. Se importó el workflow, se ejecutó mediante adaptador de entrada y se recuperó su JSON original de n8n, inactivo y con credenciales solo por nombre. No se publicó en la instancia habitual.

## Contratos de negocio con doble de IA

Los nueve `.eml` originales no se modificaron. Se parsearon como UTF-8 y se asignó un Message-ID ficticio estable a cada uno. El simulador entrega una extracción predefinida; **no mide la calidad del modelo ni demuestra acceso a OpenRouter**. El resto del recorrido consulta la API real de la copia semilla, reserva en PostgreSQL, registra abonos por API y entrega los avisos en Mailpit.

| Caso | Ejecución | Resultado observado y comprobado |
| --- | --- | --- |
| F03-01 Carmen | 100 | Un abono de 10 EUR al apartado 1 por Bizum; registro confirmado |
| F03-02 Jorge | 101 | Un abono de 20 EUR al apartado 2, identificado explícitamente; confirmado |
| F03-03 Lucía | 102 | Un abono de 12 EUR por **transferencia**, apartado 3 liquidado y pendiente cero |
| F03-04 Laura | 103 | Cero abonos, un aviso y revisión con motivo `exceso_sobre_pendiente_del_candidato` |
| F03-05 Romero | 104 | Cero abonos, un aviso y revisión por `identidad_insuficiente` |
| F03-06 Paula | 105 | Cero abonos, un aviso y revisión por `fuera_de_plazo` |
| F03-07 desconocido | 106 | Cero abonos, un aviso y revisión por `cliente_desconocido` |
| F03-08 publicidad | 107 | Cero abonos y ningún aviso |
| F03-09 Silvia | 108 | Un abono de 5 EUR al apartado 24 por Bizum; confirmado |
| F03-10 repetición | 109 | El correo de Carmen no crea otro abono |
| F03-11 IA inválida | 110; PF-08 111 | Error de extracción, cero abonos y un aviso del Error Workflow |

Los avisos de revisión se comprobaron también en el registro: estado `revision`, motivo esperado y `aviso_confirmado=true`. El test anterior (50–64) verificaba efectos pero no todos los motivos; la corrida actual amplía esa comprobación y corrige la distinción de cliente desconocido, conservando las expectativas del contrato.

## Fallos y lotes

- Ejecución **112**: el doble IA inventa 9 EUR donde el correo dice 10 EUR. El flujo rechaza la extracción, no crea abonos y PF-08 maneja el error.
- Ejecución **114**, repetición **116**: el proxy llama a la API, que registra un abono, pero retrasa la respuesta más allá del timeout. Queda exactamente un abono nuevo y se mantiene el bloqueo auxiliar; repetir el mismo correo no hace otro POST. No se borraron reservas para ocultar el resultado incierto.
- Ejecuciones **65, 66 y 67**: un lote con dos correos ficticios de publicidad produjo dos extracciones y dos ejecuciones del procesador, además del padre. Se conserva el Execute Workflow del propio flujo; solo se sustituyen IMAP y el proveedor externo. Comprueba el procesamiento por item, no una conexión IMAP real.
- Backend: **15 tests pasaron**, incluidos el abono por transferencia con liquidación y una venta por transferencia. Se conservaron los tests anteriores. La ampliación no requiere migración ni cambia pagos existentes.

Al terminar, los workflows de prueba se desactivaron y la app volvió a su base de laboratorio habitual. Las bases de prueba, registros y bloqueo de timeout quedan como evidencia en los volúmenes aislados.

## Pendiente para cerrar HU-03

1. Validar la credencial de OpenRouter en n8n y repetir los nueve correos con `openrouter/free`, sin alternativas de pago. Todavía no hay una llamada real satisfactoria al proveedor; no se atribuye coste ni precisión observados.
2. Probar el disparador IMAP con un buzón ficticio y Message-ID real estable.
3. Integrar PF-00/PF-02 de Rita y verificar el recibo tras un pago aceptado.
4. Revisión humana de Rita y merge hacia `dev` cuando se satisfagan los criterios.

Reproducción y conciliación: [configuración PF-03](../03-abonos-distancia.md). Los contratos no se cambiaron para aprobar pruebas: solo se registra la autorización explícita de `transferencia` en lugar del bloqueo anterior de F03-03.
