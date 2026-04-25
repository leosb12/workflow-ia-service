from app.core.config import get_settings
from app.modules.asistente_formularios.prompts.prompts_llenado_formulario import PromptsLlenadoFormulario
from app.modules.asistente_formularios.servicio.servicio_asistente_formularios import ServicioAsistenteFormularios
from app.modules.asistente_formularios.validadores.validador_campos_formulario import ValidadorCamposFormulario
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def obtener_servicio_asistente_formularios() -> ServicioAsistenteFormularios:
    llm_client = DeepSeekClient(settings=get_settings())
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsLlenadoFormulario()
    field_validator = ValidadorCamposFormulario()
    return ServicioAsistenteFormularios(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        field_validator=field_validator,
    )


get_servicio_asistente_formularios = obtener_servicio_asistente_formularios
get_form_ai_service = obtener_servicio_asistente_formularios
