from app.core.config import get_settings
from app.modules.analitica.prompts.prompts_analitica import PromptsAnalitica
from app.modules.analitica.servicio.servicio_analitica import ServicioAnalitica
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def obtener_servicio_analitica() -> ServicioAnalitica:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsAnalitica()
    return ServicioAnalitica(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
    )


get_servicio_analitica = obtener_servicio_analitica
get_analytics_ai_service = obtener_servicio_analitica
