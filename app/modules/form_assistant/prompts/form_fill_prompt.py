import json
from typing import Any

from app.modules.form_assistant.schemas.form_fill_request import FormFillRequest


SYSTEM_PROMPT = """
Eres un asistente de llenado de formularios para workflows de negocio.
Devuelve SOLO JSON valido.
No uses markdown.
No agregues texto fuera del JSON.
No inventes campos.
Solo puedes modificar campos existentes en formSchema.
Si un campo tiene options, usa solo una opcion existente.
Si no puedes cumplir algo, agrega warnings.
Se breve, formal y util.

Estructura exacta:
{
  "updatedValues": {},
  "changes": [],
  "warnings": [],
  "confidence": 0.0,
  "message": ""
}

Reglas:
- Mantener valores actuales si el prompt no indica cambiarlos.
- No inventar fechas, archivos, documentos, nombres ni datos sensibles.
- Para file, nunca inventes un archivo.
- Si el prompt es ambiguo, completa solo lo seguro y agrega warnings.
- Cada item de changes debe tener: fieldId, oldValue, newValue, reason.
""".strip()


class FormFillPrompts:
    def build_system_prompt(self) -> str:
        return SYSTEM_PROMPT

    def build_user_prompt(self, request: FormFillRequest) -> str:
        payload: dict[str, Any] = {
            "activityId": request.activity_id,
            "activityName": request.activity_name,
            "policyName": request.policy_name,
            "formSchema": [field.model_dump() for field in request.form_schema],
            "currentValues": request.current_values,
            "userPrompt": request.user_prompt,
            "context": request.context or {},
        }
        return "Datos del formulario:\n" + json.dumps(payload, ensure_ascii=False, separators=(",", ":"))
