# PF-08 · Avisos de error

## Estado y alcance

Propuesta. [HU-05 / #6](https://github.com/IA-P1-BCN/LUSOGIRLS-N8N/issues/6). Autora: Fabiana; revisora: Rita. Entidad auxiliar: Incidencia, con identificadores técnicos mínimos.

## Decisiones de implementación · 22/10/2026

Fabiana autoriza correo local de pruebas. Se utiliza SMTP con Mailpit (sin retransmisión externa) y PostgreSQL como registro auxiliar, separado de SQLite. Una clave primaria y `INSERT ON CONFLICT DO NOTHING RETURNING` reservan cada aviso de forma atómica. La reserva no se libera automáticamente: si el envío o su confirmación fallan, se concilia antes de volver a enviar. La ausencia de ID se agrupa por flujo y paso en ventanas de cinco minutos.

Se ejecuta el fallo automático en otra instancia n8n, proyecto Docker `lusogirls-pruebas`, con datos y puertos propios. La activación temporal se limita al emisor ficticio de pruebas. PF-08 no tiene otro Error Workflow asociado. El texto crudo del error nunca forma parte del aviso.

## Disparador y entradas

Error Trigger, seleccionado como Error Workflow en la configuración de los flujos de negocio. Entrada del error: `workflow.id/name` y, cuando existan, `execution.id/url/lastNodeExecuted/error.message`. Los errores de trigger pueden aportar otra estructura; validar presencia y usar «no disponible» cuando falte un campo.

## Procesamiento y salidas

Construir un aviso a Marisa con nombre del flujo, paso afectado, tipo/resumen seguro del error y referencia a ejecución si existe. Crear el mensaje desde una lista explícita de campos permitidos. No reenviar el payload completo, headers, cuerpo de correo, clave, stack con datos personales ni una URL con query secreta. Para errores desconocidos, preferir un resumen genérico y referencia interna.

El tratamiento de errores de negocio controlados (exceso de pago, identidad dudosa) pertenece al flujo correspondiente; esos casos pueden terminar correctamente con una incidencia y no disparar Error Trigger.

## Errores e idempotencia

Deduplicar por workflow y ejecución cuando exista ID. Si falta, usar una huella mínima y ventana documentada; no fusionar errores independientes indefinidamente. Un fallo del canal de avisos debe quedar visible en la ejecución/log sanitizado y no iniciar un bucle de avisos recursivos.

## Credenciales y variables

`PF · Notificaciones`, destinatario autorizado de Marisa y registro de incidencias sin secretos. El workflow de error no se configura a sí mismo como mecanismo recursivo.

## Pruebas y aceptación

[F08-01 y F08-02](../data/pruebas/contratos.json): error con referencia y texto sensible ficticio; error de trigger con campos ausentes. Esos payloads prueban el formato, no la integración real del Error Trigger.

- [ ] Cada flujo de negocio tiene asociado PF-08.
- [ ] Un fallo real en ejecución automática de prueba produce aviso con flujo, paso y resumen seguro.
- [ ] Se prueban campos ausentes y fallo del canal sin recursión.
- [ ] El aviso no contiene credenciales ni el payload completo.
- [ ] Se adjunta evidencia del error y del aviso; la prueba automática controlada requiere acordar su activación local y no autoriza publicar en producción.
