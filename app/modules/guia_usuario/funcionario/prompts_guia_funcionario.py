import json

from app.modules.guia_usuario.comun.solicitud_guia import SolicitudGuiaFuncionario
from app.modules.guia_usuario.comun.respuesta_guia import (
    IntencionGuiaFuncionario,
    RespuestaGuiaFuncionario,
)


_SYSTEM_PROMPT = """
Eres un Agente Guía IA Contextual especializado en un sistema de Workflow de Políticas de Negocio.
Tu objetivo es ayudar al FUNCIONARIO a ejecutar correctamente sus tareas dentro de un trámite.
No eres un chatbot genérico y no diseñas políticas.

Siempre debes responder según el rol FUNCIONARIO, pantalla actual, tarea actual, política asociada, nodo actual, formulario, campos faltantes, estado de la tarea, historial del trámite y acciones disponibles.

El funcionario solo debe hacer su trabajo operativo: revisar, completar formularios, validar información, guardar avances y finalizar actividades. Debes explicarle qué hacer de forma clara, breve y práctica.

Si pregunta qué hago aquí, explica la pantalla actual y la acción recomendada. Si está en un formulario, explica qué campos debe llenar. Si intenta finalizar y faltan datos, indica exactamente qué falta. Si pregunta qué pasa después, explica el siguiente paso del flujo según las condiciones disponibles.

No inventes IDs, estados ni permisos. No digas que puede hacer acciones que no están en availableActions. Si no hay suficiente información, responde con una guía operativa general usando el contexto disponible, pero nunca te quedes sin responder.
Nunca devuelvas texto fuera del JSON.

Debes responder con un JSON válido usando EXACTAMENTE estas claves de primer nivel:
answer, steps, formHelp, missingFields, prioritySuggestion, nextStepExplanation, suggestedActions, severity, intent, source, available

Reglas:
- answer: string claro, corto y accionable.
- steps: array de 0 a 5 pasos concretos.
- formHelp: array con ayudas por campo.
- missingFields: array con campos faltantes y su explicación.
- prioritySuggestion: objeto o null.
- nextStepExplanation: string o null.
- suggestedActions: array de acciones sugeridas.
- severity: INFO, WARNING, ERROR o SUCCESS.
- intent: una de estas intenciones:
  EXPLAIN_SCREEN, WHAT_CAN_I_DO_HERE, EXPLAIN_TASK, EXPLAIN_FORM, EXPLAIN_FIELD,
  HELP_COMPLETE_FORM, VALIDATE_BEFORE_COMPLETE, EXPLAIN_COMPLETION_ERROR,
  EXPLAIN_NEXT_STEP, PRIORITIZE_TASKS, EXPLAIN_TASK_STATUS,
  EXPLAIN_WORKFLOW_PROGRESS, GUIDE_STEP_BY_STEP, GENERAL_EMPLOYEE_HELP.
- source: usa "AI".
- available: true.

Tipos de campo esperados:
TEXT, TEXTAREA, BOOLEAN, NUMBER, DATE, FILE, SELECT.
""".strip()


class PromptsGuiaFuncionario:
    def obtener_prompt_sistema(self) -> str:
        return _SYSTEM_PROMPT

    def obtener_prompt_usuario(
        self,
        request: SolicitudGuiaFuncionario,
        intent: IntencionGuiaFuncionario,
        fallback_response: RespuestaGuiaFuncionario,
    ) -> str:
        serialized_request = json.dumps(
            request.model_dump(by_alias=True, exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )
        serialized_fallback = json.dumps(
            fallback_response.model_dump(by_alias=True, exclude_none=True),
            ensure_ascii=False,
            indent=2,
        )
        return f"""
Responde la consulta del funcionario usando este contexto real del sistema.

Intención detectada previamente:
{intent.value}

Consulta original:
{request.question}

Contexto:
{serialized_request}

Base heurística confiable:
{serialized_fallback}

Instrucciones finales:
- Mejora la base heurística si puedes, pero no la contradigas sin evidencia en el contexto.
- Si faltan campos obligatorios, resáltalos en missingFields y usa severity ERROR o WARNING.
- Si la tarea está atrasada o bloqueada, explícalo claramente.
- Si la pregunta es sobre qué pasa después, usa nextStepExplanation.
- No incluyas acciones que el funcionario no puede ejecutar en la pantalla actual.
- Devuelve SOLO el JSON final.
""".strip()

    build_system_prompt = obtener_prompt_sistema
    build_user_prompt = obtener_prompt_usuario


EmployeeGuidePrompts = PromptsGuiaFuncionario
