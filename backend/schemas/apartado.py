"""SCHEMAS · Apartado: la forma de los datos que entran y salen por la API."""

from datetime import date, datetime

from pydantic import BaseModel, Field, StrictBool

from schemas.abono import AbonoOut
from schemas.vale import ValeOut


class ApartadoIn(BaseModel):
    cliente: str
    telefono: str | None = None
    email: str | None = None
    producto: str
    talla: str | None = None
    precio: float = Field(gt=0)
    abono_inicial: float
    forma_pago: str = "efectivo"
    fecha: date | None = Field(None, description="Solo para migrar datos antiguos. Por defecto, hoy.")
    consentimiento_notificaciones: StrictBool = False


class ApartadoOut(BaseModel):
    id: int
    fecha: date
    cliente: str
    telefono: str | None
    email: str | None
    producto: str
    talla: str | None
    precio: float
    fecha_limite: date
    estado: str
    abonado: float
    pendiente: float
    consentimiento_notificaciones: bool
    consentimiento_actualizado: datetime | None


class ConsentimientoIn(BaseModel):
    consentimiento_notificaciones: StrictBool


class ConsentimientoOut(BaseModel):
    apartado_id: int
    consentimiento_notificaciones: bool
    consentimiento_actualizado: datetime | None


class ApartadoDetalle(ApartadoOut):
    abonos: list[AbonoOut]
    vale: ValeOut | None


class Vencimiento(BaseModel):
    apartado: ApartadoOut
    vale: ValeOut


class Resumen(BaseModel):
    activo: int
    liquidado: int
    vencido: int
    total: int
