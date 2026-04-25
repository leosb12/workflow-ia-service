"""Application modules organized by vertical capability.

This package keeps temporary compatibility aliases for the previous English
module layout. The service was migrated to Spanish names, but parts of the
codebase and tests still import the legacy paths. Registering the aliases here
lets old and new imports resolve to the same module objects.
"""

from importlib import import_module
import sys

_LEGACY_MODULE_ALIASES = {
    "app.modules.analytics_ai": "app.modules.analitica",
    "app.modules.analytics_ai.infrastructure": "app.modules.analitica.infraestructura",
    "app.modules.analytics_ai.infrastructure.dependencies": "app.modules.analitica.infraestructura.dependencias",
    "app.modules.analytics_ai.prompts": "app.modules.analitica.prompts",
    "app.modules.analytics_ai.prompts.analytics_prompts": "app.modules.analitica.prompts.prompts_analitica",
    "app.modules.analytics_ai.schemas": "app.modules.analitica.modelos",
    "app.modules.analytics_ai.schemas.analytics_request": "app.modules.analitica.modelos.solicitud_analitica",
    "app.modules.analytics_ai.schemas.analytics_response": "app.modules.analitica.modelos.respuesta_analitica",
    "app.modules.analytics_ai.service": "app.modules.analitica.servicio",
    "app.modules.analytics_ai.service.analytics_ai_service": "app.modules.analitica.servicio.servicio_analitica",
    "app.modules.form_assistant": "app.modules.asistente_formularios",
    "app.modules.form_assistant.prompts": "app.modules.asistente_formularios.prompts",
    "app.modules.form_assistant.prompts.form_fill_prompt": "app.modules.asistente_formularios.prompts.prompts_llenado_formulario",
    "app.modules.form_assistant.schemas": "app.modules.asistente_formularios.modelos",
    "app.modules.form_assistant.schemas.form_fill_request": "app.modules.asistente_formularios.modelos.solicitud_llenado_formulario",
    "app.modules.form_assistant.schemas.form_fill_response": "app.modules.asistente_formularios.modelos.respuesta_llenado_formulario",
    "app.modules.form_assistant.service": "app.modules.asistente_formularios.servicio",
    "app.modules.form_assistant.service.form_ai_service": "app.modules.asistente_formularios.servicio.servicio_asistente_formularios",
    "app.modules.form_assistant.validators": "app.modules.asistente_formularios.validadores",
    "app.modules.form_assistant.validators.form_field_validator": "app.modules.asistente_formularios.validadores.validador_campos_formulario",
    "app.modules.simulations_ai": "app.modules.simulacion",
    "app.modules.simulations_ai.infrastructure": "app.modules.simulacion.infraestructura",
    "app.modules.simulations_ai.infrastructure.dependencies": "app.modules.simulacion.infraestructura.dependencias",
    "app.modules.simulations_ai.prompts": "app.modules.simulacion.prompts",
    "app.modules.simulations_ai.prompts.simulation_prompts": "app.modules.simulacion.prompts.prompts_simulacion",
    "app.modules.simulations_ai.schemas": "app.modules.simulacion.modelos",
    "app.modules.simulations_ai.schemas.simulation_request": "app.modules.simulacion.modelos.solicitud_simulacion",
    "app.modules.simulations_ai.schemas.simulation_response": "app.modules.simulacion.modelos.respuesta_simulacion",
    "app.modules.simulations_ai.service": "app.modules.simulacion.servicio",
    "app.modules.simulations_ai.service.simulations_ai_service": "app.modules.simulacion.servicio.servicio_simulacion",
    "app.modules.user_guide": "app.modules.guia_usuario",
    "app.modules.user_guide.infrastructure": "app.modules.guia_usuario.infraestructura",
    "app.modules.user_guide.infrastructure.dependencies": "app.modules.guia_usuario.infraestructura.dependencias",
    "app.modules.user_guide.prompts": "app.modules.guia_usuario.prompts",
    "app.modules.user_guide.prompts.admin_guide_prompts": "app.modules.guia_usuario.prompts.prompts_guia_administrador",
    "app.modules.user_guide.prompts.employee_guide_prompts": "app.modules.guia_usuario.prompts.prompts_guia_funcionario",
    "app.modules.user_guide.schemas": "app.modules.guia_usuario.modelos",
    "app.modules.user_guide.schemas.guide_request": "app.modules.guia_usuario.modelos.solicitud_guia",
    "app.modules.user_guide.schemas.guide_response": "app.modules.guia_usuario.modelos.respuesta_guia",
    "app.modules.user_guide.service": "app.modules.guia_usuario.servicio",
    "app.modules.user_guide.service.admin_guide_fallback_service": "app.modules.guia_usuario.servicio.respaldo_guia_administrador",
    "app.modules.user_guide.service.admin_guide_intent_classifier": "app.modules.guia_usuario.servicio.clasificador_intencion_administrador",
    "app.modules.user_guide.service.admin_guide_service": "app.modules.guia_usuario.servicio.servicio_guia_administrador",
    "app.modules.user_guide.service.employee_guide_fallback_service": "app.modules.guia_usuario.servicio.respaldo_guia_funcionario",
    "app.modules.user_guide.service.employee_guide_intent_classifier": "app.modules.guia_usuario.servicio.clasificador_intencion_funcionario",
    "app.modules.user_guide.service.employee_guide_service": "app.modules.guia_usuario.servicio.servicio_guia_funcionario",
    "app.modules.workflow_generator": "app.modules.generador_flujos",
    "app.modules.workflow_generator.domain": "app.modules.generador_flujos.dominio",
    "app.modules.workflow_generator.domain.models": "app.modules.generador_flujos.dominio.validador_json_flujo",
}


def _register_legacy_module_aliases() -> None:
    for legacy_name, current_name in _LEGACY_MODULE_ALIASES.items():
        module = import_module(current_name)
        sys.modules.setdefault(legacy_name, module)

        parent_name, _, attribute_name = legacy_name.rpartition(".")
        parent_module = sys.modules.get(parent_name)
        if parent_module is not None and not hasattr(parent_module, attribute_name):
            setattr(parent_module, attribute_name, module)


_register_legacy_module_aliases()
