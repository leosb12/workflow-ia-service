from app.core.config import get_settings
from app.modules.editor_flujo_ia.dominio.validador_edicion_flujo import ValidadorEdicionFlujo
from app.modules.editor_flujo_ia.prompts.prompts_editor_flujo import PromptsEditorFlujoIa
from app.modules.editor_flujo_ia.servicio.servicio_editor_flujo import ServicioEditorFlujoIa
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def obtener_servicio_editor_flujo_ia() -> ServicioEditorFlujoIa:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsEditorFlujoIa()
    validator = ValidadorEdicionFlujo()
    return ServicioEditorFlujoIa(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        validator=validator,
    )


get_servicio_editor_flujo_ia = obtener_servicio_editor_flujo_ia
get_workflow_editor_ai_service = obtener_servicio_editor_flujo_ia

