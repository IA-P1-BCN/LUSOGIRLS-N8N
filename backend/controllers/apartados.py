"""CONTROLADOR · Apartados: la lógica de cada petición.

Recibe los datos ya validados, llama a los modelos y devuelve el resultado.
Qué URL llega a cada función se define en routes/apartados.py.
"""

from fastapi import BackgroundTasks, Response

from models import abono, apartado, vale
from schemas.abono import AbonoIn
from schemas.apartado import ApartadoIn, ConsentimientoIn
from services import n8n


def listar(response: Response, estado: str | None = None, q: str = "", pagina: int | None = None, por_pagina: int = 25):
    """Filtra por `estado` (activo, liquidado o vencido) y busca con `q`. Sin `pagina` devuelve todos.
    El total de resultados va en la cabecera `X-Total-Count`."""
    limite = por_pagina if pagina else None
    apartados, total = apartado.listar(estado, q, limite, (max(pagina or 1, 1) - 1) * por_pagina)
    response.headers["X-Total-Count"] = str(total)
    return apartados


def resumen():
    return apartado.contar_por_estado()


def ver(apartado_id: int):
    return apartado.obtener(apartado_id) | {"abonos": abono.de_apartado(apartado_id), "vale": vale.del_apartado(apartado_id)}


def crear(datos: ApartadoIn, tareas: BackgroundTasks):
    nuevo = apartado.crear(**datos.model_dump())
    tareas.add_task(n8n.avisar, "apartado.creado", nuevo)
    return nuevo


def abonar(apartado_id: int, datos: AbonoIn, tareas: BackgroundTasks):
    actualizado = abono.registrar(apartado_id, **datos.model_dump())
    tareas.add_task(n8n.avisar, "abono.registrado", actualizado | {"importe": datos.importe})
    return actualizado


def vencer(apartado_id: int, tareas: BackgroundTasks):
    resultado = apartado.vencer(apartado_id)
    tareas.add_task(n8n.avisar, "apartado.vencido", resultado)
    return resultado


def consentimiento(apartado_id: int):
    return apartado.consultar_consentimiento(apartado_id)


def cambiar_consentimiento(apartado_id: int, datos: ConsentimientoIn):
    return apartado.actualizar_consentimiento(apartado_id, datos.consentimiento_notificaciones)
