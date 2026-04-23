from app.core.config import get_settings
from app.ia.client.deepseek_client import DeepSeekClient
from app.ia.service.ia_service import IaService
from app.ia.util.workflow_validator import WorkflowJsonValidator


def get_ia_service() -> IaService:
    client = DeepSeekClient(settings=get_settings())
    validator = WorkflowJsonValidator()
    return IaService(deepseek_client=client, workflow_validator=validator)
