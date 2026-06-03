import json
from typing import Any

from app.modules.asistente_formularios.modelos.solicitud_llenado_formulario import FormFillRequest


SYSTEM_PROMPT = """
Eres un asistente de llenado de formularios para workflows de negocio.
Devuelve SOLO JSON valido.
No uses markdown.
No agregues texto fuera del JSON.
No inventes campos.
Solo puedes modificar campos existentes en formSchema.
Si un campo tiene options (tipo select), usa solo una opcion existente.
Si un campo es de tipo checkbox y tiene options, usa un arreglo (lista) con una o mas de las opciones existentes en formSchema.
Si un campo es de tipo grid, representa su valor como una matriz de strings (arreglo de arreglos, e.g. [["val1", "val2"], ["val3", "val4"]]) que represente las celdas de la tabla.
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


class PromptsLlenadoFormulario:
    def obtener_prompt_sistema(self) -> str:
        return SYSTEM_PROMPT

    def obtener_prompt_usuario(self, request: FormFillRequest) -> str:
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

    build_system_prompt = obtener_prompt_sistema
    build_user_prompt = obtener_prompt_usuario


FormFillPrompts = PromptsLlenadoFormulario
