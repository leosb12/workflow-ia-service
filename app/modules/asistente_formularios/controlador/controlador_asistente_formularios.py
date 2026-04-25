from fastapi import APIRouter, Body, Depends

from app.modules.asistente_formularios.infraestructura.dependencias import obtener_servicio_asistente_formularios
from app.modules.asistente_formularios.modelos.solicitud_llenado_formulario import FormFillRequest
from app.modules.asistente_formularios.modelos.respuesta_llenado_formulario import FormFillResponse
from app.modules.asistente_formularios.servicio.servicio_asistente_formularios import ServicioAsistenteFormularios

router = APIRouter(prefix="/api/ia/forms", tags=["ia"])


@router.post("/fill", response_model=FormFillResponse)
async def llenar_formulario_con_ia(
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
    service: ServicioAsistenteFormularios = Depends(obtener_servicio_asistente_formularios),
) -> FormFillResponse:
    handler = getattr(service, "llenar_formulario", None) or getattr(service, "fill_form")
    return await handler(request)


fill_form_with_ai = llenar_formulario_con_ia
