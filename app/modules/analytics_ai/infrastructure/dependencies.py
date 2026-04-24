from app.core.config import get_settings
from app.modules.analytics_ai.prompts.analytics_prompts import AnalyticsPrompts
from app.modules.analytics_ai.service.analytics_ai_service import AnalyticsAiService
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def get_analytics_ai_service() -> AnalyticsAiService:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = AnalyticsPrompts()
    return AnalyticsAiService(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
    )
