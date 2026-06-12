from typing import Optional
from fastapi import APIRouter, Body, Depends, Header

from app.modules.clasificador_solicitudes_orquestador.dependencias import (
    obtener_servicio_clasificador_solicitudes,
)
from app.modules.clasificador_solicitudes_orquestador.modelos import (
    IaClasificacionRequest,
    IaClasificacionResponse,
)
from app.modules.clasificador_solicitudes_orquestador.servicio import ServicioClasificadorSolicitudes

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.post("/clasificar-solicitud", response_model=IaClasificacionResponse)
async def clasificar_solicitud(
    request: IaClasificacionRequest = Body(...),
    x_ai_mode: Optional[str] = Header(None, alias="X-AI-Mode"),
    service: ServicioClasificadorSolicitudes = Depends(obtener_servicio_clasificador_solicitudes),
) -> IaClasificacionResponse:
    return await service.clasificar(request, x_ai_mode)
