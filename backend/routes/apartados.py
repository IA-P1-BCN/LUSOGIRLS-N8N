"""RUTAS · Apartados: qué URL llega a qué función del controlador."""

from fastapi import APIRouter, Depends

from controllers import apartados
from middleware.seguridad import exigir_clave
from schemas.apartado import ApartadoDetalle, ApartadoOut, ConsentimientoOut, Resumen, Vencimiento

router = APIRouter(prefix="/api/apartados", tags=["apartados"], dependencies=[Depends(exigir_clave)])

router.get("", response_model=list[ApartadoOut], summary="Lista de apartados")(apartados.listar)
router.get("/resumen", response_model=Resumen, summary="Cuántos apartados hay por estado")(apartados.resumen)
router.get("/{apartado_id}", response_model=ApartadoDetalle, summary="Un apartado con sus abonos y su vale")(apartados.ver)
router.post("", response_model=ApartadoOut, status_code=201, summary="Crear un apartado (con su abono inicial)")(apartados.crear)
router.post("/{apartado_id}/abonos", response_model=ApartadoOut, status_code=201, summary="Registrar un abono")(apartados.abonar)
router.post("/{apartado_id}/vencer", response_model=Vencimiento,
            summary="Marca un apartado fuera de plazo como vencido y genera el vale")(apartados.vencer)
router.get("/{apartado_id}/consentimiento", response_model=ConsentimientoOut,
           summary="Consulta el permiso actual para notificaciones")(apartados.consentimiento)
router.patch("/{apartado_id}/consentimiento", response_model=ConsentimientoOut,
             summary="Registra o retira el permiso de notificaciones")(apartados.cambiar_consentimiento)
