# Servicios compartidos y laboratorio

PF-03, PF-04, PF-05, PF-07 y PF-08 usan correo SMTP y un registro auxiliar PostgreSQL. La app se consulta por HTTP con Header Auth; su SQLite no se modifica directamente. Estas decisiones permiten compartir los mismos servicios con los flujos de Rita sin duplicar el Webhook `tienda`.

## En el entorno del equipo

Añadir una contraseña aleatoria `REGISTRO_PASSWORD` al `.env` local (no subirlo). Iniciar:

```bash
docker compose -f docker-compose.yml -f infra/automatizaciones.compose.yml up -d
```

En n8n configurar las credenciales locales:

| Nombre | Tipo y parámetros |
| --- | --- |
| PF · Registro auxiliar | Postgres: host `registro`, puerto 5432, DB `automatizaciones`, usuario `n8n`, contraseña del `.env`; conexión solo en la red Docker local |
| PF · Notificaciones | SMTP: host `correo`, puerto 1025, SSL/TLS desactivado, Disable STARTTLS activado; sin usuario/contraseña en Mailpit local |
| PF · API tienda | Header Auth: nombre `X-API-Key`, valor de `API_KEY` local |

Ver correos ficticios en `http://localhost:8025`. Mailpit no retransmite mensajes al exterior. El SMTP y Postgres no publican puertos en el ordenador. Sus credenciales no se ponen en nodos ni Git. Cambiar a un proveedor real requiere configuración y autorización del destinatario.

Importar primero PF-08, seleccionar credenciales, y elegirlo en Settings → Error Workflow de cada flujo de negocio. PF-08 no se asocia a sí mismo. La importación mantiene los workflows sin publicar. Para activación autorizada, n8n 2.44.5 requiere publicar también PF-08; validar antes en el laboratorio.

La tabla `pf_config` guarda configuración no secreta, incluida `UMBRAL_VENTA_GRANDE`. No se asigna un umbral de negocio por defecto. Ejemplo **de pruebas**, cambiable sin editar nodos:

```sql
INSERT INTO pf_config(clave,valor) VALUES ('UMBRAL_VENTA_GRANDE','100')
ON CONFLICT(clave) DO UPDATE SET valor=excluded.valor;
```

`pf_registro` reserva cada clave con exclusión atómica. Estados: `reservado` antes del efecto y `confirmado` después; `revision` para conciliación. Una repetición no vuelve a enviar ni a cobrar. No existe una transacción única que englobe SMTP o la API de la tienda: si se corta la conexión tras el efecto, conservar la reserva y conciliar. Para recuperar un aviso, comprobar primero ejecución y buzón; solo con ausencia de envío demostrada se autoriza una nueva tentativa sobre la misma operación. No borrar reservas automáticamente ni cambiar la clave para forzar un reintento. El documento del cierre queda guardado aunque falle SMTP.

## Puesta en marcha: errores frecuentes

Observados al levantar una instancia local con `dev` en `613a23c` y n8n 2.45.4 (`docs/pruebas/2026-10-29-instancia-local-hu14.md`).

- **Subflujos sin publicar.** PF-00, PF-01 y PF-02 (y PF-04 y PF-06 si se usan) deben estar publicados. Si falta uno, PF-00 falla con «Workflow is not active and cannot be executed» y PF-08 avisa del paso `Ejecutar PF-01` (o el que corresponda).
- **Credencial del Webhook.** Crear `PF · Webhook tienda` (Header Auth, cabecera `X-PF-Webhook-Key`, valor igual a `N8N_WEBHOOK_KEY` del `.env`) antes de importar `workflows/00-entrada-eventos.json` y `workflows/09-migracion.json`. Después, abrir `Recibir eventos` y `Recibir migración` y comprobar que usan esa credencial y no `PF · API tienda`.
- **Importar sobre un flujo existente.** Vaciar antes el lienzo (Ctrl/Cmd+A y Supr). Si no, los nodos importados se pegan junto a los antiguos.
- **URL del webhook.** Con PF-00 publicado, `N8N_WEBHOOK_URL=http://n8n:5678/webhook/tienda`; con el listener de prueba, `http://n8n:5678/webhook-test/tienda`. Aplicar el cambio recreando solo `tienda`. Ver [Webhook: probar y publicar son acciones distintas](../workflows/README.md#webhook-probar-y-publicar-son-acciones-distintas).
- **Sin clave no hay eventos.** Si `N8N_WEBHOOK_KEY` está vacía, la app no envía ningún evento y deja en el log de `tienda` «No se pudo avisar a n8n (…): falta configurar la autenticación» (`backend/services/n8n.py`).
- **Error Workflow.** Los JSON se exportan sin `errorWorkflow`. Elegir PF-08 a mano en **Settings → Error Workflow** de cada flujo de negocio, nunca en el propio PF-08.
- **PF-06.** Publicarlo activa su calendario diario (`0 9 * * *`, 09:00 Europe/Madrid), que vence por API los apartados fuera de plazo y la app genera sus vales. Sin publicarlo, un evento `apartado.vencido` falla en PF-00 con el mismo error que PF-01 sin publicar, y avisa PF-08. Para probarlo sin publicar, ejecutarlo a mano.

## Laboratorio reproducible

```bash
python3 tests/n8n/preparar.py
docker compose --env-file tests/n8n/.env.local -f tests/n8n/compose.yml up -d
python3 tests/n8n/lab.py
python3 tests/n8n/lab.py 08
```

Puertos solo en loopback: n8n 15678, Mailpit 18025 y tienda 18000. Proyecto y volúmenes propios `lusogirls-pruebas`; los de `paso-firme` se conservan. `.env.local` se crea con permisos 600; el script no muestra su secreto. Las credenciales del laboratorio se crean mediante la API de esa instancia, nunca reutilizando la sesión personal. Los tests usan su API interna, verificada en 2.44.5; pueden requerir adaptación al actualizar n8n. La imagen instalada se reutiliza en el laboratorio; comprobar su versión al reproducir.

Detener sin borrar evidencia:

```bash
docker compose --env-file tests/n8n/.env.local -f tests/n8n/compose.yml stop
```

Referencias: [Postgres y parámetros de consulta](https://docs.n8n.io/integrations/builtin/app-nodes/n8n-nodes-base.postgres/), [exportación de workflows](https://docs.n8n.io/workflows/export-import/).
