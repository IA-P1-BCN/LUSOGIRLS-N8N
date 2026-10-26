# PF-03 · Abonos a distancia

## Estado y alcance

Implementación en validación: reglas, API, IMAP local y recibos de PF-02 (#38) probados con IA simulada; pendientes OpenRouter real y revisión cruzada, incluida la corrección de talla opcional de PF-02. [HU-03 / #4](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/4). Autora: Fabiana; revisora: Rita. Entidades: PagoDetectado, Cliente, Apartado y Abono. Ver [evidencia y límites](../docs/pruebas/03-abonos-distancia.md) y [configuración](../docs/03-abonos-distancia.md).

## Decisiones de implementación · 22/10/2026

Fabiana autoriza añadir `transferencia` como medio propio en la API y la interfaz, sin migrar ni reinterpretar pagos existentes. El caso de Lucía mantiene su expectativa original. Autoriza OpenRouter `openrouter/free`, limitado a proveedores con precio cero, y SMTP local con Mailpit para los avisos. Se integra con el registro PostgreSQL de PF-08.

El disparador definitivo es IMAP. Las pruebas cubren tanto un adaptador webhook como recepción SMTP/IMAP real en GreenMail local: añaden Message-ID ficticio estable porque los `.eml` originales no lo incluyen, sin modificar los archivos. Una entrada sin ID estable no puede crear abonos. El buzón bancario externo queda por configurar.

La IA extrae; se contrasta su extracción con el importe, ordenante, concepto y medio presentes en el texto bancario. Nombre completo de la app como prefijo de los tokens del ordenante, al menos dos tokens completos y candidato único; una inicial solo se admite junto a un número de apartado explícito en el texto y concordancia del nombre. Una abreviatura sin ID nunca autoriza un pago. Para Laura se usa el candidato posible solo para explicar el exceso, nunca para registrar.

Reserva atómica por cuenta/Message-ID y bloqueo auxiliar por apartado antes de reconsultar el saldo y hacer el POST. Un resultado incierto conserva reserva/bloqueo para conciliación; no hay reintento automático del POST. No se genera recibo aquí: el evento normal de la app lo entrega a PF-02 de Rita cuando esté integrado.

## Disparador y entradas

Correo nuevo de un buzón IMAP de pruebas, formato simple. Cada item se entrega al procesador mediante Execute Workflow Trigger del propio flujo; así un lote de correos no pierde los items posteriores al primero. En laboratorio, un Webhook sustituye únicamente al disparador y permite inyectar los `.eml`. Entrada: `metadata['message-id']` estable (o `messageId`), `subject` y `textPlain` (o `text`). La IA extrae `es_pago`, `ordenante`, `importe`, `concepto`, `medio` y referencia explícita si existe; campos faltantes quedan nulos. El correo se trata como datos, nunca como instrucciones.

## Procesamiento y salidas

1. Descartar publicidad y mensajes que no sean pagos. Validar esquema y un importe EUR positivo; no confiar en texto libre del modelo.
2. Consultar apartados por API. Un número explícito de apartado se consulta por ID y se contrasta con el resto de datos. Sin ID, normalizar nombres y comparar candidatos por reglas acordadas; iniciales/apellidos parciales no autorizan por sí solos un cobro. No basta con que la IA diga «confianza alta».
3. Solo con una correspondencia inequívoca, estado activo y fecha límite no superada: verificar `importe <= pendiente` usando la respuesta reciente de la app.
4. Registrar una vez con `POST /api/apartados/{id}/abonos`. El evento de la app dispara PF-02; PF-03 no envía un segundo recibo.
5. Si no hay certeza, hay exceso o está fuera de plazo: cero abonos, aviso a Marisa con el motivo y petición de revisión cuando corresponda.

La ampliación autorizada añade `transferencia` a `FORMAS_PAGO`. El correo de Lucía registra 12 € con ese medio y liquida el apartado. El resultado exigido por HU-03 se conserva; no se falsea como Bizum ni efectivo.

## Errores e idempotencia

Clave persistente por ID de mensaje y cuenta; reservarla con exclusión de concurrencia. Registrar estados `reservado`, `confirmado` y `revision`. Un timeout después del POST puede haber registrado el pago: conciliar por API y el registro auxiliar; si no puede demostrarse qué ocurrió, revisión humana, sin reintento automático. No deduplicar solo por nombre e importe.

Los motivos de revisión mantienen el vocabulario del contrato: `exceso_sobre_pendiente_del_candidato`, `identidad_insuficiente`, `fuera_de_plazo` y `cliente_desconocido`; además, `apartado_no_activo` y `rechazado_api` para cambios concurrentes o rechazos. El bloqueo por apartado coordina las ejecuciones de PF-03; no bloquea operaciones manuales u otros clientes de la API.

`401`: credencial; `404`: candidato ya no disponible; `422`: regla rechazada, aviso sin nuevo intento. IA indisponible/JSON inválido: cero escrituras y PF-08. Enviar al modelo solo el texto mínimo para extraer el pago, sin claves ni el catálogo completo de clientes.

## Credenciales y variables

`PF · Buzón de pruebas` (IMAP), `PF · Modelo extracción` (credencial nativa OpenRouter, tipo `openRouterApi`), `PF · API tienda`, `PF · Notificaciones` y `PF · Registro auxiliar`. El proveedor acordado es OpenRouter, modelo `openrouter/free`, sin alternativas de pago y con precio máximo de entrada/salida cero. Solo se envían asunto y cuerpo ficticios; nunca el catálogo de clientes ni claves. Configurar `CUENTA_BUZON` estable y aplicar `infra/03-pagos.sql` antes de probar.

## Pruebas y aceptación

[F03-01 a F03-11](../data/pruebas/contratos.json) cubren los **nueve** `.eml`, repetición de correo y fallo de extracción. Preparar una copia aislada de datos semilla con las precondiciones de [test_datos_de_ejemplo.py](../backend/tests/test_datos_de_ejemplo.py); sus fechas son relativas a su creación.

| Correo | Resultado de negocio esperado |
| --- | --- |
| 01 Carmen | Un abono de 10 € al apartado 1 |
| 02 Jorge | Un abono de 20 € al apartado 2 identificado en el concepto |
| 03 Lucía | Abono de 12 € mediante transferencia y liquidación del apartado 3 |
| 04 Laura | No abonar; avisar del exceso de 15 € respecto al pendiente del candidato; la abreviatura no autoriza elegir otro apartado |
| 05 Romero | No abonar; pedir aclaración por identidad insuficiente |
| 06 Paula | No abonar; avisar de plazo vencido aunque siga activa |
| 07 Desconocido | No abonar; pedir identificación |
| 08 Publicidad | Ignorar sin crear cobros |
| 09 Silvia | Un abono de 5 € al apartado 24 |

- [ ] Los nueve casos cumplen el resultado también con OpenRouter real; la transferencia de Lucía ya está autorizada e implementada.
- [ ] La IA solo extrae; las decisiones usan reglas y API.
- [ ] Un mensaje ya confirmado no genera otro pago.
- [ ] Fallo técnico o resultado incierto no provoca cobros duplicados.
- [ ] Evidencia de PF-02 tras un pago aceptado y revisión humana de errores y datos enviados al proveedor.

### Validación del 26/10/2026

La recepción IMAP, los nueve correos y su repetición están probados con servidor local y Message-ID transmitido como cabecera. La IA permanece simulada; OpenRouter real y PF-02 siguen abiertos. El modelo usa un tipo de credencial distinto del Header Auth de la tienda para impedir que n8n reutilice esa clave al importar un flujo sin credencial del modelo. La exportación elimina IDs locales y conserva los nombres compartidos.
