from app.ia.service.ia_service import IaService
from app.modules.workflow_generator.application.generate_workflow_usecase import (
    GenerateWorkflowUseCase,
)
from app.modules.workflow_generator.infrastructure.dependencies import (
    get_generate_workflow_usecase,
)


def get_ia_service() -> IaService:
    return IaService(use_case=get_generate_workflow_usecase())


def get_generate_workflow_service() -> GenerateWorkflowUseCase:
    return get_generate_workflow_usecase()
