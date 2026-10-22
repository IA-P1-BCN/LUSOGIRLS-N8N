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
