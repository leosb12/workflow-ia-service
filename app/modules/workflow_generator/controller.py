from fastapi import APIRouter, Depends

from app.modules.workflow_generator.application.generate_workflow_usecase import (
    GenerateWorkflowUseCase,
)
from app.modules.workflow_generator.infrastructure.dependencies import (
    get_generate_workflow_usecase,
)
from app.modules.workflow_generator.schemas import TextoAFlujoRequest, TextoAFlujoResponse

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.post("/texto-a-flujo", response_model=TextoAFlujoResponse)
async def convertir_texto_a_flujo(
    request: TextoAFlujoRequest,
    use_case: GenerateWorkflowUseCase = Depends(get_generate_workflow_usecase),
) -> TextoAFlujoResponse:
    return await use_case.execute(request)
