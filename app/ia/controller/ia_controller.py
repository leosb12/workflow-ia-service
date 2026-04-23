from fastapi import APIRouter, Depends

from app.ia.dependencies import get_ia_service
from app.ia.dto.texto_a_flujo import TextoAFlujoRequest, TextoAFlujoResponse
from app.ia.service.ia_service import IaService

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.post("/texto-a-flujo", response_model=TextoAFlujoResponse)
async def convertir_texto_a_flujo(
    request: TextoAFlujoRequest,
    ia_service: IaService = Depends(get_ia_service),
) -> TextoAFlujoResponse:
    return await ia_service.convertir_texto_a_flujo(request)
