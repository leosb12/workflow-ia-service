from app.core.config import get_settings
from app.modules.workflow_generator.application.generate_workflow_usecase import (
    GenerateWorkflowUseCase,
)
from app.modules.workflow_generator.domain.models import WorkflowJsonValidator
from app.modules.workflow_generator.domain.prompts import WorkflowPrompts
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def get_generate_workflow_usecase() -> GenerateWorkflowUseCase:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    workflow_validator = WorkflowJsonValidator()
    json_parser = JsonObjectParser()
    prompts = WorkflowPrompts()
    return GenerateWorkflowUseCase(
        prompt_runner=prompt_runner,
        workflow_validator=workflow_validator,
        json_parser=json_parser,
        prompts=prompts,
    )
