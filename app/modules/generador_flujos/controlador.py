from fastapi import APIRouter, Depends

from app.modules.generador_flujos.aplicacion.caso_uso_generar_flujo import (
    CasoUsoGenerarFlujo,
)
from app.modules.generador_flujos.infraestructura.dependencias import (
    obtener_caso_uso_generar_flujo,
)
from app.modules.generador_flujos.modelos import TextoAFlujoRequest, TextoAFlujoResponse

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.post("/texto-a-flujo", response_model=TextoAFlujoResponse)
async def convertir_texto_a_flujo(
    request: TextoAFlujoRequest,
    use_case: CasoUsoGenerarFlujo = Depends(obtener_caso_uso_generar_flujo),
) -> TextoAFlujoResponse:
    return await use_case.ejecutar(request)
