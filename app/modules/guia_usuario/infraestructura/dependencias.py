from app.core.config import get_settings
from app.modules.guia_usuario.administrador.respaldo_guia_administrador import (
    RespaldoGuiaAdministrador,
)
from app.modules.guia_usuario.administrador.clasificador_intencion_administrador import (
    ClasificadorIntencionAdministrador,
)
from app.modules.guia_usuario.administrador.prompts_guia_administrador import PromptsGuiaAdministrador
from app.modules.guia_usuario.administrador.servicio_guia_administrador import ServicioGuiaAdministrador
from app.modules.guia_usuario.funcionario.respaldo_guia_funcionario import (
    RespaldoGuiaFuncionario,
)
from app.modules.guia_usuario.funcionario.clasificador_intencion_funcionario import (
    ClasificadorIntencionFuncionario,
)
from app.modules.guia_usuario.funcionario.prompts_guia_funcionario import PromptsGuiaFuncionario
from app.modules.guia_usuario.funcionario.servicio_guia_funcionario import ServicioGuiaFuncionario
from app.modules.guia_usuario.usuario_movil.respaldo_guia_usuario_movil import (
    RespaldoGuiaUsuarioMovil,
)
from app.modules.guia_usuario.usuario_movil.clasificador_intencion_usuario_movil import (
    ClasificadorIntencionUsuarioMovil,
)
from app.modules.guia_usuario.usuario_movil.prompts_guia_usuario_movil import PromptsGuiaUsuarioMovil
from app.modules.guia_usuario.usuario_movil.servicio_guia_usuario_movil import ServicioGuiaUsuarioMovil
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def obtener_servicio_guia_administrador() -> ServicioGuiaAdministrador:
    settings = get_settings()
    llm_client = DeepSeekClient(settings=settings)
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsGuiaAdministrador()
    classifier = ClasificadorIntencionAdministrador()
    fallback_service = RespaldoGuiaAdministrador()
    return ServicioGuiaAdministrador(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        classifier=classifier,
        fallback_service=fallback_service,
        llm_model=settings.deepseek_user_guide_model,
    )


def obtener_servicio_guia_funcionario() -> ServicioGuiaFuncionario:
    settings = get_settings()
    llm_client = DeepSeekClient(settings=settings)
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsGuiaFuncionario()
    classifier = ClasificadorIntencionFuncionario()
    fallback_service = RespaldoGuiaFuncionario()
    return ServicioGuiaFuncionario(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        classifier=classifier,
        fallback_service=fallback_service,
        llm_model=settings.deepseek_user_guide_model,
    )


def obtener_servicio_guia_usuario_movil() -> ServicioGuiaUsuarioMovil:
    settings = get_settings()
    llm_client = DeepSeekClient(settings=settings)
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = PromptsGuiaUsuarioMovil()
    classifier = ClasificadorIntencionUsuarioMovil()
    fallback_service = RespaldoGuiaUsuarioMovil()
    return ServicioGuiaUsuarioMovil(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        classifier=classifier,
        fallback_service=fallback_service,
        llm_model=settings.deepseek_user_guide_model,
    )


get_servicio_guia_administrador = obtener_servicio_guia_administrador
get_servicio_guia_funcionario = obtener_servicio_guia_funcionario
get_servicio_guia_usuario_movil = obtener_servicio_guia_usuario_movil
get_admin_guide_service = obtener_servicio_guia_administrador
get_employee_guide_service = obtener_servicio_guia_funcionario
get_mobile_user_guide_service = obtener_servicio_guia_usuario_movil
