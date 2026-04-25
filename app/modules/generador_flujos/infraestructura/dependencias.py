from app.core.config import get_settings
from app.modules.generador_flujos.aplicacion.caso_uso_generar_flujo import (
    CasoUsoGenerarFlujo,
)
from app.modules.generador_flujos.dominio.validador_json_flujo import ValidadorJsonFlujo
from app.modules.generador_flujos.dominio.prompts_generador_flujos import PromptsGeneradorFlujos
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def obtener_caso_uso_generar_flujo() -> CasoUsoGenerarFlujo:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    workflow_validator = ValidadorJsonFlujo()
    json_parser = JsonObjectParser()
    prompts = PromptsGeneradorFlujos()
    return CasoUsoGenerarFlujo(
        prompt_runner=prompt_runner,
        workflow_validator=workflow_validator,
        json_parser=json_parser,
        prompts=prompts,
    )


get_caso_uso_generar_flujo = obtener_caso_uso_generar_flujo
