from fastapi import APIRouter, Body, Depends

from app.modules.form_assistant.infrastructure.dependencies import get_form_ai_service
from app.modules.form_assistant.schemas.form_fill_request import FormFillRequest
from app.modules.form_assistant.schemas.form_fill_response import FormFillResponse
from app.modules.form_assistant.service.form_ai_service import FormAiService

router = APIRouter(prefix="/api/ia/forms", tags=["ia"])


@router.post("/fill", response_model=FormFillResponse)
async def fill_form_with_ai(
    request: FormFillRequest = Body(
        ...,
        openapi_examples={
            "rechazo_con_documentos": {
                "summary": "Rechazo con observacion y documentos",
                "value": {
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
                        "currentDepartment": "Legal",
                        "userRole": "funcionario",
                    },
                },
            }
        },
    ),
    service: FormAiService = Depends(get_form_ai_service),
) -> FormFillResponse:
    return await service.fill_form(request)
