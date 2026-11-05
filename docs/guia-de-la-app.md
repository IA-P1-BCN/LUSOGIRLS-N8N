# Guía de la app de la tienda

Este documento explica **cómo funciona la app de Paso Firme** para que sepáis qué os da, cómo habla con n8n y dónde mirar cuando algo no sale. El enunciado del proyecto (el problema, las reglas del negocio, los flujos y los niveles) está en el [README](../README.md).

> **No tenéis que programar la app.** Tenéis que entenderla, porque n8n va a conversar con ella todo el tiempo.

---

## 1. La app en un minuto

La app es el **mostrador digital** de la zapatería: ahí se apuntan apartados, abonos y ventas. Hace tres cosas:

| Qué hace | Cómo |
|---|---|
| **Guarda los datos y aplica las reglas** | Base de datos SQLite. No deja abonar de más, ni abonar por debajo del mínimo, ni abonar un apartado fuera de plazo |
| **Se deja consultar y manejar desde fuera** | Una **API REST** (`/api/...`) protegida con una clave. Es lo que usa n8n, y también la pantalla |
| **Avisa cuando pasa algo** | Un **webhook**: manda un `POST` a n8n cada vez que se crea un apartado, se abona, se vence o se vende |

La conversación va en las dos direcciones:

```
            avisos (webhook)  ─── "ha pasado esto" ───▶
   APP  ◀─────────────────────────────────────────────  n8n
            API REST  ◀── "dame / registra / vence esto" ──
```

| Dirección | Para qué sirve | Cuándo |
|---|---|---|
| **App → n8n** (webhook) | Que n8n **reaccione** en el momento: mandar la confirmación, el recibo... | Cuando ocurre algo en la tienda |
| **n8n → app** (API) | Que n8n **consulte o actúe**: pedir los apartados que vencen, vencer uno, registrar un abono... | Cuando n8n lo decide (por ejemplo, cada mañana) |

---

## 2. Direcciones: qué es cada cosa

Cuando levantáis el proyecto (`docker compose up -d`, ver [Cómo empezar](../README.md#-cómo-empezar)) se encienden **dos contenedores**:

| Servicio | Desde tu navegador o terminal | Desde dentro de n8n | Para qué |
|---|---|---|---|
| La app | http://localhost:8000 | `http://tienda:8000` | Pantallas y API |
| Swagger (documentación de la API) | http://localhost:8000/docs | `http://tienda:8000/docs` | Probar cada endpoint con un botón |
| n8n | http://localhost:5678 | `http://n8n:5678` | Construir las automatizaciones |

> ⚠️ **La trampa del `localhost`.** Cada contenedor es como una casa distinta y `localhost` significa «esta casa». Para n8n, `localhost` es **n8n mismo**, no la tienda. Por eso, **dentro de n8n** (nodo HTTP Request) se escribe `http://tienda:8000/...`, usando el nombre del servicio. Y por la misma razón la app avisa a n8n en `http://n8n:5678/...`.

---

## 3. Cómo está organizada la app (MVC)

No hace falta tocar el código, pero ayuda saber qué hay dentro. La app separa responsabilidades. Piensa en un restaurante:

| Pieza | Carpeta | En el restaurante | Qué hace |
|---|---|---|---|
| **M**odelo | `backend/models/`, `backend/database.py` | La cocina | Guarda los datos y aplica las reglas (abono mínimo de 5 €, plazo de 90 días...) |
| Schemas | `backend/schemas/` | La comanda | La forma exacta de los datos que entran y salen (con Pydantic) |
| Rutas | `backend/routes/` | El plano de la sala | Dice qué mesa (URL) atiende qué camarero (función): «los apartados nuevos los lleva `crear`» |
| **C**ontrolador | `backend/controllers/` | El camarero | La lógica de cada petición: se la pasa a la cocina y devuelve la respuesta |
| Middleware | `backend/middleware/` | El portero | Actúa antes o alrededor: comprueba la clave de la API y convierte los errores en respuestas claras |
| **V**ista | `frontend/` | El comedor y la carta | Lo que ve y usa la dependienta: HTML, CSS y JavaScript |
| `main.py` | `backend/main.py` | El encargado | Solo junta las piezas, no tiene lógica |
| Servicio | `backend/services/n8n.py` | El repartidor | Es quien **envía el webhook** a n8n |

La idea clave: **la interfaz no tiene reglas ni toca la base de datos**. Pide todo a la API, igual que lo hará n8n. La pantalla y n8n son dos clientes del mismo camarero:

```
 Pantalla (frontend/) ─┐                 ┌─ middleware/ (clave)
                       ├──▶ routes/ ──▶ controllers/ ──▶ models/ ──▶ base de datos
 n8n ──────────────────┘
```

Por eso la carpeta se llama `frontend/` y no `templates/`: no son plantillas que rellena el servidor, es una interfaz que **consulta la API**.

---

## 4. Los apartados: reglas y estados

### Reglas que aplica la app

| Regla | Detalle |
|---|---|
| Abono inicial | Mínimo **5 €** al crear el apartado, y no más que el precio |
| Plazo | `fecha_limite` = fecha del apartado **+ 90 días** |
| Abonos | De cualquier importe, pero **nunca más de lo que falta** |
| Formas de pago | `efectivo`, `tarjeta`, `bizum` o `transferencia` (ampliación de HU-03 autorizada el 22/10/2026) |
| Abonar | Solo si el apartado está `activo` **y** no ha pasado su fecha límite |

Si una regla no se cumple, la app responde con un error `422` y un mensaje claro (ver [errores](#errores-que-puede-devolver-la-api)).

### Estados

Un apartado siempre está en uno de estos tres estados (campo `estado`):

```
                 el abono deja lo pendiente en 0 €
   ┌─────────┐ ───────────────────────────────────▶ ┌────────────┐
   │ activo  │                                       │ liquidado  │  (puede recoger sus zapatos)
   └─────────┘ ───────────────────────┐              └────────────┘
                                      │ POST /vencer, solo si ya pasó la fecha límite
                                      ▼
                                ┌───────────┐
                                │  vencido  │  (se genera un vale con lo que había abonado)
                                └───────────┘
```

Conviene fijarse en dos cosas:

- **`liquidado` lo pone la app sola**, en cuanto un abono deja lo pendiente en 0 €. Nadie tiene que hacer nada.
- **`vencido` NO lo pone la app sola.** Un apartado cuyo plazo ha pasado **sigue `activo`** hasta que alguien llama a `POST /api/apartados/{id}/vencer`. Esa es una de las tareas de n8n (flujo «Recordatorios y vencimientos»).
- `liquidado` y `vencido` son finales: ya no admiten abonos.

---

## 5. La API (n8n → app)

Todo lo que n8n puede pedirle a la app. La documentación interactiva, con botón para probar cada endpoint, está en http://localhost:8000/docs (pulsad **Authorize** y escribid el valor de `API_KEY`).

### Seguridad

Cada petición a `/api/...` necesita la cabecera:

```
X-API-Key: <el valor de API_KEY de tu .env>
```

En n8n se hace **una vez**, creando una credencial *Header Auth* (Name `X-API-Key`, Value tu clave) y eligiéndola en los nodos HTTP Request. Sin clave, o con una incorrecta, la app responde `401`.

### Endpoints

| Endpoint | Para qué |
|---|---|
| `GET /api/apartados` | Lista de apartados |
| `GET /api/apartados/resumen` | Cuántos hay por estado (`activo`, `liquidado`, `vencido`, `total`) |
| `GET /api/apartados/{id}` | Un apartado, con sus **abonos** y su **vale** (o `null`) |
| `GET/PATCH /api/apartados/{id}/consentimiento` | Consultar o registrar/retirar el permiso de correo de ese apartado |
| `POST /api/apartados` | Crear un apartado (con su abono inicial) |
| `POST /api/apartados/{id}/abonos` | Registrar un abono |
| `POST /api/apartados/{id}/vencer` | Vencer un apartado fuera de plazo y generar su vale |
| `GET /api/abonos` | Abonos entre dos fechas |
| `GET /api/ventas` | Ventas entre dos fechas |
| `POST /api/ventas` | Registrar una venta |
| `GET /api/vales` | Vales de compra generados |
| `GET /api/excel` | Descargar todos los datos en un Excel |

### Parámetros de las consultas (`GET`)

| Endpoint | Parámetros (todos opcionales) |
|---|---|
| `/api/apartados` | `estado` (`activo`, `liquidado` o `vencido`), `q` (busca por cliente, producto, teléfono o nº), `pagina`, `por_pagina` |
| `/api/abonos` | `desde`, `hasta` (formato `AAAA-MM-DD`, ambas incluidas) |
| `/api/ventas` | `desde`, `hasta`, `orden` (`asc` o `desc`), `pagina`, `por_pagina` |

> 💡 **Sin `pagina` devuelve todo**, en una lista. n8n recibe cada elemento de la lista como **un item** (un apartado = un item), que es justo lo que necesitas para recorrerlos. El total de resultados va en la cabecera de respuesta `X-Total-Count`.

### Qué hay que enviar en los `POST`

| Endpoint | Cuerpo (JSON) |
|---|---|
| `POST /api/apartados` | `cliente`, `producto`, `precio`, `abono_inicial` (obligatorios) · `telefono`, `email`, `talla`, `forma_pago`, `fecha`, `consentimiento_notificaciones` (opcionales; permiso false por defecto) |
| `POST /api/apartados/{id}/abonos` | `importe` (obligatorio) · `forma_pago`, `fecha` |
| `POST /api/ventas` | `concepto`, `importe` (obligatorios) · `forma_pago`, `fecha` |
| `POST /api/apartados/{id}/vencer` | Sin cuerpo |

`fecha` sirve **solo para migrar datos antiguos** (por ejemplo, el Excel de Marisa): permite crear algo con su fecha original. Si no se envía, la app usa hoy.

### Qué devuelve un apartado

```json
{
  "id": 25, "fecha": "2026-10-20",
  "cliente": "Carmen Ruiz", "telefono": "612 345 001", "email": "carmen@example.com",
  "producto": "Botín piel marrón", "talla": "38",
  "precio": 89.9, "abonado": 30.0, "pendiente": 59.9,
  "fecha_limite": "2027-01-18", "estado": "activo"
}
```

`abonado` y `pendiente` los **calcula la app** a partir de los abonos. **No los recalculéis en n8n**: usad los que llegan.

El detalle (`GET /api/apartados/{id}`) añade los abonos y el vale:

```json
{ "...": "los campos de arriba", 
  "abonos": [ {"id": 84, "apartado_id": 25, "fecha": "2026-10-20", "importe": 10.0, "forma_pago": "bizum"} ],
  "vale": null }
```

### Errores que puede devolver la API

Todos tienen la misma forma, `{"detail": "..."}`, con un mensaje que se puede leer y mostrar:

| Código | Cuándo | Ejemplo de `detail` |
|---|---|---|
| `401` | Falta la clave o es incorrecta | `Falta la cabecera X-API-Key o no es válida` |
| `404` | No existe lo que se pide | `Apartado no encontrado` |
| `422` | Una regla del negocio no se cumple | `El abono inicial mínimo es de 5 €` |

> En n8n, por defecto, un `4xx` **detiene el flujo** con error. Si queréis tratarlo (por ejemplo, avisar a Marisa en lugar de fallar), en el nodo HTTP Request, **Settings → On Error → Continue (using error output)**.

---

## 6. El webhook (app → n8n)

### Qué pasa y cuándo

Cada vez que ocurre algo, la app envía un `POST` con un JSON a la dirección que pone `N8N_WEBHOOK_URL` en el `.env` (por defecto `http://n8n:5678/webhook/tienda`). El JSON siempre tiene la misma forma:

```json
{ "evento": "<qué ha pasado>", "datos": { ... } }
```

| Evento | Cuándo se envía | Qué lleva `datos` |
|---|---|---|
| `apartado.creado` | Se crea un apartado | El apartado |
| `abono.registrado` | Se registra un abono | El apartado ya actualizado **+ `importe`** (lo que se acaba de abonar) |
| `venta.registrada` | Se registra una venta directa | La venta |
| `apartado.vencido` | Se vence un apartado | `{ "apartado": {...}, "vale": {...} }` |

Se envían **tanto si la acción viene de la pantalla como de la API**: da igual quién la haga.

### Cómo se le envían los estados a n8n

El estado **va dentro de los datos**, en el campo `datos.estado`, y es **el estado después de la acción**. Eso es lo que permite decidir con un nodo IF o Switch sin consultar nada más:

| Evento | Ejemplo | Qué se puede decidir en n8n |
|---|---|---|
| `abono.registrado` | `"estado": "activo"`, `"pendiente": 59.9` | Todavía debe: mandar el recibo con lo que falta |
| `abono.registrado` | `"estado": "liquidado"`, `"pendiente": 0` | Ya está pagado: avisar de que puede recoger sus zapatos |
| `apartado.vencido` | `"estado": "vencido"` y un `vale` | Avisar con el código y el importe del vale |

Los cuatro avisos tal y como salen de la app:

**`apartado.creado`**

```json
{"evento": "apartado.creado", "datos": {"id": 25, "fecha": "2026-10-20", "cliente": "Carmen Ruiz", "telefono": "612 345 001", "email": "carmen@example.com", "producto": "Botín piel marrón", "talla": "38", "precio": 89.9, "fecha_limite": "2027-01-18", "estado": "activo", "abonado": 10.0, "pendiente": 79.9}}
```

**`abono.registrado`** (fijaos en el `importe` del final)

```json
{"evento": "abono.registrado", "datos": {"id": 25, "fecha": "2026-10-20", "cliente": "Carmen Ruiz", "telefono": "612 345 001", "email": "carmen@example.com", "producto": "Botín piel marrón", "talla": "38", "precio": 89.9, "fecha_limite": "2027-01-18", "estado": "activo", "abonado": 30.0, "pendiente": 59.9, "importe": 20.0}}
```

**`venta.registrada`**

```json
{"evento": "venta.registrada", "datos": {"id": 257, "fecha": "2026-10-20", "concepto": "Crema calzado", "importe": 4.5, "forma_pago": "efectivo"}}
```

**`apartado.vencido`** (aquí `datos` tiene dos partes)

```json
{"evento": "apartado.vencido", "datos": {"apartado": {"id": 16, "cliente": "Paula Ramos", "email": "paula16@example.com", "producto": "Zapatilla running azul", "precio": 64.5, "abonado": 5.0, "pendiente": 59.5, "estado": "vencido", "...": "..."}, "vale": {"id": 2, "codigo": "VALE-00016", "apartado_id": 16, "fecha": "2026-10-20", "importe": 5.0, "usado": 0}}}
```

### Cómo lo recibe n8n

1. Un nodo **Webhook** con método `POST` y **Path** `tienda` (para que coincida con `http://n8n:5678/webhook/tienda`).
2. n8n guarda lo recibido dentro de **`body`**. Por eso, para leerlo, se escribe `{{ $json.body.evento }}` y `{{ $json.body.datos.estado }}`, **no** `{{ $json.evento }}`.
3. Un nodo **Switch** sobre `{{ $json.body.evento }}` reparte cada evento a su camino.

### Test URL y Production URL

El nodo Webhook tiene dos direcciones, y se confunden mucho:

| | Dirección | Funciona cuando... |
|---|---|---|
| **Test URL** | `http://n8n:5678/webhook-test/tienda` | Has pulsado **Listen for test event** o **Execute workflow** (solo un aviso cada vez) |
| **Production URL** | `http://n8n:5678/webhook/tienda` | El flujo está **publicado** (*Publish*) |

La app usa **la Production URL** (es lo que trae el `.env`). Por eso, **si el flujo no está publicado, n8n responde 404 y no pasa nada.**

### Lo que conviene saber (y es una trampa habitual)

- **El aviso se envía una sola vez, sin reintentos.** Si n8n está apagado o el flujo sin publicar en ese momento, **ese aviso se pierde**. La app no lo vuelve a intentar. Por eso los flujos programados (el cierre, los vencimientos) **no deben depender de haber recibido el aviso**: consultan la API.
- **La app no se entera de si n8n lo procesó bien.** Solo le importa enviarlo. Si n8n falla por dentro, la app ni lo sabe.
- **Un fallo del aviso no rompe nada en la tienda.** Crear un apartado funciona igual aunque n8n esté caído. El aviso se manda **después** de responder a la dependienta, con un máximo de 5 segundos de espera.
- Si `N8N_WEBHOOK_URL` está **vacía** en el `.env`, la app no envía ningún aviso.

### Cómo ver qué está enviando la app

| Qué quieres saber | Dónde mirar |
|---|---|
| ¿Ha llegado el aviso a n8n? | En n8n, pestaña **Executions** del flujo (si está publicado) |
| ¿Cómo es exactamente el aviso? | Pulsa **Listen for test event** en el nodo Webhook, y mira su **Output** al llegar el aviso (usa la Test URL: ver abajo) |
| ¿Ha fallado el envío? | En la terminal: `docker compose logs tienda`. Si n8n no responde o contesta con un error (por ejemplo, 404), aparece **«No se pudo avisar a n8n»** |

Para ver los avisos con la **Test URL** mientras construís el flujo, cambiad en el `.env`:

```
N8N_WEBHOOK_URL=http://n8n:5678/webhook-test/tienda
```

y aplicad el cambio con `docker compose up -d`. Cuando el flujo esté publicado, **volved a poner** `/webhook/tienda`.

---

## 7. Datos de ejemplo

La primera vez que arranca, la app se llena sola con unos meses de actividad de la tienda (24 apartados y unas 250 ventas), con fechas **relativas al día en que la levantéis**. Así siempre hay:

- apartados que vencen **dentro de 7 días** y **mañana** (para los recordatorios),
- apartados **fuera de plazo** que siguen `activo` (para que vuestro flujo los venza),
- apartados `liquidado`, uno ya `vencido` con su vale, y ventas y abonos de **hoy** y de los **meses anteriores** (para el cierre diario y el informe mensual).

Los clientes de ejemplo tienen correos `@example.com`: **para recibir vosotros los mensajes, cread un apartado nuevo con vuestro correo.**

| Quiero... | Cómo |
|---|---|
| Empezar de cero y recargar los datos de ejemplo | `docker compose down -v` y luego `docker compose up -d` (⚠️ borra también tus flujos de n8n) |
| Arrancar con la app vacía | `SEED=0` en el `.env` |

---

## 8. Probar la app sin n8n

Desde la terminal, para ver qué responde la API y qué avisos dispara. Cada comando se pega tal cual. Cambiad `cambia-esta-clave` si habéis puesto otra `API_KEY`.

**Crear un apartado** (devuelve su `id`; los comandos siguientes usan el 25, cambiadlo por el vuestro):

```bash
curl -X POST http://localhost:8000/api/apartados \
  -H "X-API-Key: cambia-esta-clave" -H "Content-Type: application/json" \
  -d '{"cliente":"Tu Nombre","email":"tu@correo.example","producto":"Botín piel marrón","talla":"38","precio":89.9,"abono_inicial":10,"forma_pago":"bizum"}'
```

**Registrar un abono:**

```bash
curl -X POST http://localhost:8000/api/apartados/25/abonos \
  -H "X-API-Key: cambia-esta-clave" -H "Content-Type: application/json" \
  -d '{"importe":20,"forma_pago":"efectivo"}'
```

**Ver el apartado con sus abonos:**

```bash
curl http://localhost:8000/api/apartados/25 -H "X-API-Key: cambia-esta-clave"
```

**Ver los apartados activos que ya pasaron su fecha límite** (candidatos a vencer; busca los que tienen `fecha_limite` anterior a hoy):

```bash
curl "http://localhost:8000/api/apartados?estado=activo" -H "X-API-Key: cambia-esta-clave"
```

**Vencer un apartado fuera de plazo** (cambiad el 16 por uno de la lista anterior):

```bash
curl -X POST http://localhost:8000/api/apartados/16/vencer -H "X-API-Key: cambia-esta-clave"
```

**Provocar un error** (abono inicial por debajo del mínimo) para ver cómo responde:

```bash
curl -X POST http://localhost:8000/api/apartados \
  -H "X-API-Key: cambia-esta-clave" -H "Content-Type: application/json" \
  -d '{"cliente":"X","producto":"Y","precio":50,"abono_inicial":2}'
```

Cada acción que cree algo dispara su aviso a n8n, igual que si se hiciera desde la pantalla.

---

## 9. Preguntas que suelen salir

| Pregunta | Respuesta |
|---|---|
| **¿Por qué n8n no encuentra la app con `http://localhost:8000`?** | Dentro de n8n `localhost` es n8n mismo. Usad `http://tienda:8000` (ver [la trampa del `localhost`](#2-direcciones-qué-es-cada-cosa)) |
| **Creo un apartado en la pantalla y no llega nada a n8n** | Lo más probable: el flujo no está **publicado** (la Production URL da 404). Mirad `docker compose logs tienda` |
| **El apartado de Carmen venció hace semanas y sigue `activo`** | Es lo esperado: `vencido` solo lo pone la llamada a `POST /vencer`. Es una tarea de n8n |
| **`401` en todas las llamadas** | La credencial de n8n no tiene la misma clave que `API_KEY` del `.env`, o el *Name* no es exactamente `X-API-Key` |
| **¿Puede n8n modificar la base de datos directamente?** | No, ni falta que hace: todo pasa por la API, que es quien aplica las reglas |
| **¿Dónde está el código que calcula `pendiente`?** | En `backend/models/apartado.py` (la consulta `SELECT`). La app lo calcula; n8n solo lo lee |

## Consentimiento y webhook autenticado (HU-14)

El alta acepta `consentimiento_notificaciones` como booleano estricto, false por defecto. `GET/PATCH /api/apartados/{id}/consentimiento` permiten consultar y registrar/retirar permiso, con clave API. Los eventos incluyen el booleano actual; n8n lo revalida antes de enviar correo. `N8N_WEBHOOK_KEY` configura la cabecera secreta `X-PF-Webhook-Key`; sin clave no se envía el evento. No hay reintentos ni cambia el resultado de la operación en tienda. Ver [configuración y límites](datos-personales.md).
