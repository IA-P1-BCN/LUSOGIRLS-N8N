# PF-03 · Abonos a distancia

## Estado y alcance

Propuesta con una discrepancia bloqueante para transferencias. [HU-03 / #4](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/4). Autora: Fabiana; revisora: Rita. Entidades: PagoDetectado, Cliente, Apartado y Abono.

## Disparador y entradas

Correo nuevo de un buzón de pruebas Gmail/IMAP; Form Trigger solo como adaptador temporal. Entrada: ID estable del mensaje, asunto, cuerpo y metadatos necesarios. La IA extrae `es_pago`, `ordenante`, `importe`, `concepto`, `medio` y referencia explícita si existe; campos faltantes quedan nulos. El correo se trata como datos, nunca como instrucciones.

## Procesamiento y salidas

1. Descartar publicidad y mensajes que no sean pagos. Validar esquema y un importe EUR positivo; no confiar en texto libre del modelo.
2. Consultar apartados por API. Un número explícito de apartado se consulta por ID y se contrasta con el resto de datos. Sin ID, normalizar nombres y comparar candidatos por reglas acordadas; iniciales/apellidos parciales no autorizan por sí solos un cobro. No basta con que la IA diga «confianza alta».
3. Solo con una correspondencia inequívoca, estado activo y fecha límite no superada: verificar `importe <= pendiente` usando la respuesta reciente de la app.
4. Registrar una vez con `POST /api/apartados/{id}/abonos`. El evento de la app dispara PF-02; PF-03 no envía un segundo recibo.
5. Si no hay certeza, hay exceso o está fuera de plazo: cero abonos, aviso a Marisa con el motivo y petición de revisión cuando corresponda.

La API solo admite `efectivo`, `tarjeta`, `bizum`. El correo de Lucía pide una transferencia que debe liquidar 12 €; **no enviar `forma_pago=transferencia` ni falsearla como otro medio**. La ejecución de ese caso queda bloqueada hasta acordar y documentar una adaptación. El resultado exigido por HU-03 sigue siendo liquidar correctamente, no cambiar el contrato para darlo por aprobado.

## Errores e idempotencia

Clave persistente por ID de mensaje y cuenta; reservarla con exclusión de concurrencia. Registrar estados pendiente/confirmado/revisión. Un timeout después del POST puede haber registrado el pago: conciliar por API y el registro auxiliar; si no puede demostrarse qué ocurrió, revisión humana, sin reintento automático. No deduplicar solo por nombre e importe.

`401`: credencial; `404`: candidato ya no disponible; `422`: regla rechazada, aviso sin nuevo intento. IA indisponible/JSON inválido: cero escrituras y PF-08. Enviar al modelo solo el texto mínimo para extraer el pago, sin claves ni el catálogo completo de clientes.

## Credenciales y variables

`PF · Buzón de pruebas`, `PF · Modelo extracción`, `PF · API tienda`, `PF · Notificaciones` y registro persistente de pagos. Elegir proveedor/modelo y reglas de identidad antes de implementar.

## Pruebas y aceptación

[F03-01 a F03-11](../data/pruebas/contratos.json) cubren los **nueve** `.eml`, repetición de correo y fallo de extracción. Preparar una copia aislada de datos semilla con las precondiciones de [test_datos_de_ejemplo.py](../backend/tests/test_datos_de_ejemplo.py); sus fechas son relativas a su creación.

| Correo | Resultado de negocio esperado |
| --- | --- |
| 01 Carmen | Un abono de 10 € al apartado 1 |
| 02 Jorge | Un abono de 20 € al apartado 2 identificado en el concepto |
| 03 Lucía | Abono de 12 € y liquidación del apartado 3; bloqueado hasta resolver el medio de pago |
| 04 Laura | No abonar; avisar del exceso de 15 € respecto al pendiente del candidato; la abreviatura no autoriza elegir otro apartado |
| 05 Romero | No abonar; pedir aclaración por identidad insuficiente |
| 06 Paula | No abonar; avisar de plazo vencido aunque siga activa |
| 07 Desconocido | No abonar; pedir identificación |
| 08 Publicidad | Ignorar sin crear cobros |
| 09 Silvia | Un abono de 5 € al apartado 24 |

- [ ] Los nueve casos cumplen el resultado, incluido Lucía cuando se resuelva la dependencia.
- [ ] La IA solo extrae; las decisiones usan reglas y API.
- [ ] Un mensaje ya confirmado no genera otro pago.
- [ ] Fallo técnico o resultado incierto no provoca cobros duplicados.
- [ ] Evidencia de PF-02 tras un pago aceptado y revisión humana de errores y datos enviados al proveedor.
