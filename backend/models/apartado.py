"""MODELO · Apartado: los datos de un apartado de zapatos y las reglas para crearlo y vencerlo."""

from datetime import date, datetime, timedelta, timezone

import config
import database
from models import vale
from models.errores import NoEncontrado, ReglaDeNegocio

# Cada apartado con lo abonado y lo pendiente, calculados a partir de sus abonos.
SELECT = """
SELECT a.*, ROUND(COALESCE(SUM(b.importe), 0), 2) AS abonado,
       ROUND(a.precio - COALESCE(SUM(b.importe), 0), 2) AS pendiente
FROM apartados a LEFT JOIN abonos b ON b.apartado_id = a.id
"""


def obtener(apartado_id):
    encontrados = database.consultar(SELECT + " WHERE a.id = ? GROUP BY a.id", apartado_id)
    if not encontrados:
        raise NoEncontrado("Apartado no encontrado")
    return encontrados[0] | {'consentimiento_notificaciones': bool(encontrados[0]['consentimiento_notificaciones'])}


def listar(estado=None, q="", limite=None, desplazamiento=0):
    """Devuelve (apartados, total). `q` busca por cliente, producto, teléfono o número."""
    condiciones, args = [], []
    if estado:
        condiciones.append("a.estado = ?")
        args.append(estado)
    if q.strip():
        condiciones.append("(a.cliente LIKE ? OR a.producto LIKE ? OR a.telefono LIKE ? OR CAST(a.id AS TEXT) = ?)")
        args += [f"%{q.strip()}%"] * 3 + [q.strip().lstrip("#")]
    filtro = (" WHERE " + " AND ".join(condiciones)) if condiciones else ""
    total = database.consultar("SELECT COUNT(*) AS n FROM apartados a" + filtro, *args)[0]["n"]
    sql = SELECT + filtro + " GROUP BY a.id ORDER BY a.fecha_limite"
    if limite:
        sql += " LIMIT ? OFFSET ?"
        args += [limite, desplazamiento]
    filas = database.consultar(sql, *args)
    return [fila | {'consentimiento_notificaciones': bool(fila['consentimiento_notificaciones'])} for fila in filas], total


def contar_por_estado():
    cuentas = {f["estado"]: f["n"] for f in database.consultar("SELECT estado, COUNT(*) AS n FROM apartados GROUP BY estado")}
    return {"activo": cuentas.get("activo", 0), "liquidado": cuentas.get("liquidado", 0),
            "vencido": cuentas.get("vencido", 0), "total": sum(cuentas.values())}


def crear(cliente, telefono, email, producto, talla, precio, abono_inicial, forma_pago, fecha=None, consentimiento_notificaciones=False):
    fecha = fecha or date.today()
    if precio <= 0:
        raise ReglaDeNegocio("El precio debe ser mayor que 0")
    if abono_inicial < config.ABONO_MINIMO:
        raise ReglaDeNegocio(f"El abono inicial mínimo es de {config.ABONO_MINIMO} €")
    if abono_inicial > precio:
        raise ReglaDeNegocio("El abono inicial no puede superar el precio")
    if forma_pago not in config.FORMAS_PAGO:
        raise ReglaDeNegocio(f"Forma de pago no válida: {forma_pago}")
    with database.conectar() as con:
        cur = con.execute(
            "INSERT INTO apartados (fecha, cliente, telefono, email, producto, talla, precio, fecha_limite, consentimiento_notificaciones, consentimiento_actualizado)"
            " VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (fecha.isoformat(), cliente.strip(), telefono, email, producto.strip(), talla, precio,
             (fecha + timedelta(days=config.PLAZO_DIAS)).isoformat(), int(consentimiento_notificaciones),
             datetime.now(timezone.utc).isoformat() if consentimiento_notificaciones else None))
        apartado_id = cur.lastrowid
        con.execute("INSERT INTO abonos (apartado_id, fecha, importe, forma_pago) VALUES (?, ?, ?, ?)",
                    (apartado_id, fecha.isoformat(), abono_inicial, forma_pago))
        if abono_inicial == precio:
            con.execute("UPDATE apartados SET estado = 'liquidado' WHERE id = ?", (apartado_id,))
    return obtener(apartado_id)


def consultar_consentimiento(apartado_id):
    filas = database.consultar(
        'SELECT id AS apartado_id, consentimiento_notificaciones, consentimiento_actualizado FROM apartados WHERE id = ?',
        apartado_id)
    if not filas:
        raise NoEncontrado('Apartado no encontrado')
    return filas[0] | {'consentimiento_notificaciones': bool(filas[0]['consentimiento_notificaciones'])}


def actualizar_consentimiento(apartado_id, consentimiento_notificaciones):
    consultar_consentimiento(apartado_id)
    with database.conectar() as con:
        con.execute('UPDATE apartados SET consentimiento_notificaciones = ?, consentimiento_actualizado = ? WHERE id = ?',
                    (int(consentimiento_notificaciones), datetime.now(timezone.utc).isoformat(), apartado_id))
    return consultar_consentimiento(apartado_id)


def vencer(apartado_id):
    """Marca como vencido un apartado fuera de plazo y genera el vale con lo abonado."""
    actual = obtener(apartado_id)
    if actual["estado"] != "activo":
        raise ReglaDeNegocio(f"El apartado ya está {actual['estado']}")
    if date.today().isoformat() <= actual["fecha_limite"]:
        raise ReglaDeNegocio(f"El apartado no vence hasta el {actual['fecha_limite']}")
    with database.conectar() as con:
        con.execute("UPDATE apartados SET estado = 'vencido' WHERE id = ?", (apartado_id,))
        con.execute("INSERT INTO vales (codigo, apartado_id, fecha, importe) VALUES (?, ?, ?, ?)",
                    (f"VALE-{apartado_id:05d}", apartado_id, date.today().isoformat(), actual["abonado"]))
    return {"apartado": obtener(apartado_id), "vale": vale.del_apartado(apartado_id)}
