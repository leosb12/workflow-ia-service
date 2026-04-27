from pydantic import ValidationError

from app.modules.asistente_formularios.modelos.solicitud_llenado_formulario import FormFillRequest


def test_form_fill_request_accepts_uppercase_and_spanish_field_types() -> None:
    request = FormFillRequest.model_validate(
        {
            "activityId": "task_1",
            "activityName": "Revision",
            "policyName": "Politica demo",
            "formSchema": [
                {
                    "id": "decision",
                    "label": "Decision",
                    "type": "SELECT",
                    "required": True,
                    "options": ["aprobado", "rechazado"],
                },
                {
                    "id": "observaciones",
                    "label": "Observaciones",
                    "type": "TEXTAREA",
                    "required": False,
                    "options": None,
                },
                {
                    "id": "requiereDocumentos",
                    "label": "Requiere documentos",
                    "type": "BOOLEANO",
                    "required": False,
                },
            ],
            "currentValues": {
                "decision": None,
                "observaciones": "",
                "requiereDocumentos": None,
            },
            "userPrompt": "Rechaza la solicitud",
        }
    )

    assert [field.type for field in request.form_schema] == ["select", "textarea", "boolean"]
    assert request.form_schema[1].options == []


def test_form_fill_request_still_rejects_invalid_field_type() -> None:
    try:
        FormFillRequest.model_validate(
            {
                "activityId": "task_1",
                "activityName": "Revision",
                "policyName": "Politica demo",
                "formSchema": [
                    {
                        "id": "decision",
                        "label": "Decision",
                        "type": "unsupported_type",
                        "required": True,
                    }
                ],
                "currentValues": {"decision": None},
                "userPrompt": "Completa el formulario",
            }
        )
    except ValidationError:
        return

    raise AssertionError("Se esperaba un ValidationError para un tipo de campo invalido.")
