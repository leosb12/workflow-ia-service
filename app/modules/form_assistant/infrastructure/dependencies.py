from app.core.config import get_settings
from app.modules.form_assistant.prompts.form_fill_prompt import FormFillPrompts
from app.modules.form_assistant.service.form_ai_service import FormAiService
from app.modules.form_assistant.validators.form_field_validator import FormFieldValidator
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def get_form_ai_service() -> FormAiService:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = FormFillPrompts()
    field_validator = FormFieldValidator()
    return FormAiService(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        field_validator=field_validator,
    )
