from app.modules.workflow_generator.application.generate_workflow_usecase import (
    GenerateWorkflowUseCase,
)


class IaService:
    def __init__(self, use_case: GenerateWorkflowUseCase) -> None:
        self.use_case = use_case

    async def convertir_texto_a_flujo(self, request):
        return await self.use_case.execute(request)
