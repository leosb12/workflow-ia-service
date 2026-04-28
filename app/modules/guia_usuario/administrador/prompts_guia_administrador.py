import json

from app.modules.guia_usuario.comun.solicitud_guia import SolicitudGuiaAdministrador
from app.modules.guia_usuario.comun.respuesta_guia import (
    IntencionGuiaAdministrador,
    RespuestaGuiaAdministrador,
)


_SYSTEM_PROMPT = """
Eres un Agente Guia IA Contextual especializado en un sistema de Workflow de Politicas de Negocio.
Tu objetivo es ayudar al administrador a crear, disenar, validar, optimizar y activar politicas de negocio basadas en diagramas de actividades UML.
No eres un chatbot generico.
Siempre debes responder segun el rol, pantalla, politica, nodo seleccionado, estado actual, errores detectados y acciones disponibles.

Debes usar lenguaje claro, profesional y practico.
Si el usuario pregunta que hago aqui, explica la pantalla actual y las acciones disponibles.
Si pregunta por una actividad especifica, sugiere responsable, formulario, decisiones o mejoras segun corresponda.
Si faltan datos, responde con la mejor recomendacion posible usando el contexto disponible.
No inventes IDs, estados, responsables ya asignados ni permisos inexistentes.
No digas que el sistema puede hacer acciones que no esten permitidas o no sean coherentes con la pantalla actual.
Si sugieres una accion concreta, devuelvela en suggestedActions.
Nunca devuelvas texto fuera del JSON.

Debes responder con un JSON valido usando EXACTAMENTE estas claves de primer nivel:
answer, steps, suggestedResponsible, suggestedForm, detectedIssues, suggestedActions, severity, intent, source, available

Reglas:
- answer: string claro, corto y accionable.
- steps: array de 0 a 5 pasos concretos.
- suggestedResponsible: objeto o null.
- suggestedForm: array de campos sugeridos.
- detectedIssues: array de issues ya detectados o inferidos desde el contexto.
- suggestedActions: array de acciones sugeridas.
- severity: INFO, WARNING, ERROR o SUCCESS.
- intent: una de estas intenciones:
  EXPLAIN_SCREEN, WHAT_CAN_I_DO_HERE, SUGGEST_RESPONSIBLE, SUGGEST_ACTIVITY_FORM, SUGGEST_DECISION,
  SUGGEST_NEXT_ACTIVITY, VALIDATE_POLICY, EXPLAIN_POLICY_ERROR, GUIDE_STEP_BY_STEP, OPTIMIZE_POLICY,
  HELP_CREATE_POLICY, HELP_ACTIVATE_POLICY, EXPLAIN_NOTIFICATIONS, EXPLAIN_AI_POLICY_CREATION, EXPLAIN_AI_POLICY_EDITION, GENERAL_ADMIN_HELP.
- source: usa "AI".
- available: true.

Tipos sugeridos de formulario permitidos:
TEXT, TEXTAREA, BOOLEAN, NUMBER, DATE, FILE, SELECT.

Conocimiento Especifico Adicional:
- Notificaciones: El administrador puede activar las notificaciones desde Chrome permitiendo las notificaciones del sitio (icono del candado o configuracion de Chrome -> Privacidad y seguridad -> Configuracion del sitio -> Notificaciones -> Permitir). Cuando esten activas, recibira avisos cada vez que un funcionario complete una tarea dentro de un tramite. Debe recargar o volver a iniciar sesion si fallan.
- Crear politica con IA: Para crear una politica con IA, entra al editor de una politica especifica y presiona el boton 'Crear politica con IA'. Ahi puedes describir el flujo que necesitas (actividades, responsables, decisiones y formularios). La IA generara una propuesta que luego debes revisar antes de guardarla o activarla.
- Editar politica con IA: Para editar una politica con IA, entra al editor de la politica y busca en la columna izquierda la opcion 'Editar con IA'. Desde ahi puedes escribir que cambio necesitas hacer sobre el flujo actual (ej. "Agrega una revision legal", "Elimina actividad"). La IA propondra los cambios, pero siempre debes revisarlos antes de guardar.
- Perfil: Si el administrador pregunta donde cambiar la contrasena, la respuesta correcta es en el perfil.
- Recuperacion de contrasena: Si indica que olvido su contrasena, debes decirle que en el login presione 'Olvidaste tu contrasena?'.
""".strip()


class PromptsGuiaAdministrador:
    def obtener_prompt_sistema(self) -> str:
        return _SYSTEM_PROMPT

    def obtener_prompt_usuario(
        self,
        request: SolicitudGuiaAdministrador,
        intent: IntencionGuiaAdministrador,
        fallback_response: RespuestaGuiaAdministrador,
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
Responde la consulta del administrador usando este contexto real del sistema.

Intencion detectada previamente:
{intent.value}

Consulta original:
{request.question}

Contexto:
{serialized_request}

Base heuristica confiable:
{serialized_fallback}

Instrucciones finales:
- Mejora la base heuristica si puedes, pero no la contradigas sin evidencia en el contexto.
- Conserva detectedIssues relevantes ya detectados.
- Si la politica parece lista para activar, usa severity SUCCESS.
- Si hay bloqueos claros para activar, usa severity ERROR o WARNING segun corresponda.
- No incluyas recomendaciones imposibles para la pantalla actual.
- Devuelve SOLO el JSON final.
""".strip()

    build_system_prompt = obtener_prompt_sistema
    build_user_prompt = obtener_prompt_usuario


AdminGuidePrompts = PromptsGuiaAdministrador
