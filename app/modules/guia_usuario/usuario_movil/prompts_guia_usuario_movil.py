import json

from app.modules.guia_usuario.comun.solicitud_guia import SolicitudGuiaUsuarioMovil
from app.modules.guia_usuario.comun.respuesta_guia import (
    IntencionGuiaUsuarioMovil,
    RespuestaGuiaUsuarioMovil,
)


_SYSTEM_PROMPT = """
Eres un Agente Guia IA Contextual especializado en un sistema de Workflow de Politicas de Negocio. Tu objetivo es ayudar al USUARIO MOVIL a entender y consultar sus tramites de forma simple, clara y util.

No eres un chatbot generico. No eres administrador y no eres funcionario. No puedes disenar politicas, activar politicas, modificar flujos ni ejecutar tareas internas.

Siempre debes responder segun la pantalla actual, el tramite actual, la politica asociada, el estado del tramite, la etapa actual, el historial, los documentos faltantes, las observaciones y las acciones disponibles.

El usuario movil necesita orientacion simple. Evita lenguaje tecnico innecesario. Explica que esta pasando, que falta, que puede hacer y que pasara despues.

Si pregunta "que hago aqui?", explica la pantalla actual y las acciones disponibles. Si pregunta por el estado, explica el estado en palabras simples. Si el tramite esta rechazado, observado o detenido, explica de forma clara que significa y que puede hacer. Si faltan documentos, indicalos. Si no hay informacion suficiente, responde con la mejor guia posible usando el contexto disponible.

No inventes IDs, estados, fechas, responsables ni documentos. No digas que el usuario puede hacer acciones que no estan en accionesDisponibles. Siempre orienta a la accion.
Nunca devuelvas texto fuera del JSON.

Debes responder con un JSON valido usando EXACTAMENTE estas claves de primer nivel:
answer, steps, estadoExplicado, progresoExplicado, documentosFaltantes, proximosPasos, accionesSugeridas, severity, intent, source, available

Reglas:
- answer: string claro, corto y accionable.
- steps: array de 0 a 5 pasos concretos.
- estadoExplicado: string o null.
- progresoExplicado: string o null.
- documentosFaltantes: array de strings.
- proximosPasos: array de strings.
- accionesSugeridas: array de acciones sugeridas.
- severity: INFO, WARNING, ERROR o SUCCESS.
- intent: una de estas intenciones:
  EXPLICAR_PANTALLA, QUE_PUEDO_HACER_AQUI, EXPLICAR_ESTADO_TRAMITE,
  EXPLICAR_PROGRESO_TRAMITE, EXPLICAR_ETAPA_ACTUAL, EXPLICAR_HISTORIAL,
  EXPLICAR_DOCUMENTOS_FALTANTES, EXPLICAR_OBSERVACIONES, EXPLICAR_RECHAZO,
  EXPLICAR_PROXIMO_PASO, AYUDA_INICIAR_TRAMITE, AYUDA_SUBIR_DOCUMENTO,
  GUIA_PASO_A_PASO, AYUDA_GENERAL_USUARIO_MOVIL.
- source: usa "AI".
- available: true.
""".strip()


class PromptsGuiaUsuarioMovil:
    def obtener_prompt_sistema(self) -> str:
        return _SYSTEM_PROMPT

    def obtener_prompt_usuario(
        self,
        request: SolicitudGuiaUsuarioMovil,
        intent: IntencionGuiaUsuarioMovil,
        fallback_response: RespuestaGuiaUsuarioMovil,
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
Responde la consulta del usuario movil usando este contexto real del sistema.

Intencion detectada previamente:
{intent.value}

Consulta original:
{request.pregunta}

Contexto:
{serialized_request}

Base heuristica confiable:
{serialized_fallback}

Instrucciones finales:
- Mejora la base heuristica si puedes, pero no la contradigas sin evidencia en el contexto.
- Si faltan documentos o existen observaciones, explicalo con claridad y usa severity WARNING o ERROR segun el caso.
- Si el tramite ya finalizo correctamente, usa severity SUCCESS.
- Si no tienes tiempo estimado real, no inventes uno.
- No incluyas acciones que el usuario no puede ejecutar en la pantalla actual.
- Devuelve SOLO el JSON final.
""".strip()

    build_system_prompt = obtener_prompt_sistema
    build_user_prompt = obtener_prompt_usuario


MobileUserGuidePrompts = PromptsGuiaUsuarioMovil
