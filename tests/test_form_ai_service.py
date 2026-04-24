import asyncio

from app.modules.form_assistant.prompts.form_fill_prompt import FormFillPrompts
from app.modules.form_assistant.schemas.form_fill_request import FormFillRequest
from app.modules.form_assistant.service.form_ai_service import FormAiService
from app.modules.form_assistant.validators.form_field_validator import FormFieldValidator
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("provider unavailable")


class StaticPromptRunner:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        return self.payload


def build_request() -> FormFillRequest:
    return FormFillRequest.model_validate(
        {
            "activityId": "task_legal_1",
            "activityName": "Revision legal",
            "policyName": "Instalacion de medidor",
            "formSchema": [
                {
                    "id": "decision",
                    "label": "Decision",
                    "type": "select",
                    "required": True,
                    "options": ["aprobado", "rechazado", "observado"],
                },
                {
                    "id": "observations",
                    "label": "Observaciones",
                    "type": "textarea",
                    "required": False,
                    "options": [],
                },
                {
                    "id": "requiresDocuments",
                    "label": "Requiere documentos adicionales",
                    "type": "boolean",
                    "required": False,
                    "options": [],
                },
            ],
            "currentValues": {
                "decision": None,
                "observations": "",
                "requiresDocuments": None,
            },
            "userPrompt": "Rechaza la solicitud y pon una explicacion de que faltan documentos legales.",
            "context": {
                "tramiteId": "tramite_001",
            },
        }
    )


def test_form_ai_service_uses_safe_fallback_when_llm_fails() -> None:
    service = FormAiService(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=FormFillPrompts(),
        field_validator=FormFieldValidator(),
    )

    response = asyncio.run(service.fill_form(build_request()))

    assert response.success is True
    assert response.updated_values["decision"] == "rechazado"
    assert response.updated_values["requiresDocuments"] is True
    assert "falta de documentos" in response.updated_values["observations"].lower()
    assert response.changes
    assert response.warnings


def test_form_ai_service_ignores_invalid_fields_from_llm() -> None:
    service = FormAiService(
        prompt_runner=StaticPromptRunner(
            """
            {
              "updatedValues": {
                "decision": "rechazado",
                "fakeField": "x"
              },
              "changes": [
                {
                  "fieldId": "decision",
                  "oldValue": null,
                  "newValue": "rechazado",
                  "reason": "El usuario solicito rechazar."
                }
              ],
              "warnings": [],
              "confidence": 0.9,
              "message": "ok"
            }
            """
        ),
        json_parser=JsonObjectParser(),
        prompts=FormFillPrompts(),
        field_validator=FormFieldValidator(),
    )

    response = asyncio.run(service.fill_form(build_request()))

    assert "fakeField" not in response.updated_values
    assert any("campo inexistente" in warning.lower() for warning in response.warnings)


def test_form_ai_service_returns_only_real_changes() -> None:
    service = FormAiService(
        prompt_runner=StaticPromptRunner(
            """
            {
              "updatedValues": {
                "decision": "rechazado",
                "observations": "",
                "requiresDocuments": null
              },
              "changes": [
                {
                  "fieldId": "decision",
                  "oldValue": null,
                  "newValue": "rechazado",
                  "reason": "El usuario solicito rechazar."
                }
              ],
              "warnings": [],
              "confidence": 0.9,
              "message": "ok"
            }
            """
        ),
        json_parser=JsonObjectParser(),
        prompts=FormFillPrompts(),
        field_validator=FormFieldValidator(),
    )

    response = asyncio.run(service.fill_form(build_request()))

    assert response.updated_values == {"decision": "rechazado"}
    assert len(response.changes) == 1


def test_form_ai_service_guides_when_prompt_is_too_generic() -> None:
    request = FormFillRequest.model_validate(
        {
            "activityId": "task_price_1",
            "activityName": "Carga comercial",
            "policyName": "Alta de servicio",
            "formSchema": [
                {
                    "id": "price",
                    "label": "Precio",
                    "type": "number",
                    "required": True,
                    "options": [],
                }
            ],
            "currentValues": {
                "price": 0,
            },
            "userPrompt": "quiero que me rellenes el formulario como sea",
            "context": {},
        }
    )

    service = FormAiService(
        prompt_runner=StaticPromptRunner(
            """
            {
              "updatedValues": {},
              "changes": [],
              "warnings": [],
              "confidence": 0.4,
              "message": "El prompt no proporciona informacion suficiente para modificar el formulario."
            }
            """
        ),
        json_parser=JsonObjectParser(),
        prompts=FormFillPrompts(),
        field_validator=FormFieldValidator(),
    )

    response = asyncio.run(service.fill_form(request))

    assert response.updated_values == {}
    assert not response.changes
    assert any("valores concretos" in warning.lower() for warning in response.warnings)
    assert "precio" in response.message.lower()
