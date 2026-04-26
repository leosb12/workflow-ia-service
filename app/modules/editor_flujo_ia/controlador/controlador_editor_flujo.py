from fastapi import APIRouter, Body, Depends

from app.modules.editor_flujo_ia.infraestructura.dependencias import obtener_servicio_editor_flujo_ia
from app.modules.editor_flujo_ia.modelos.respuesta_edicion_flujo import RespuestaEdicionFlujo
from app.modules.editor_flujo_ia.modelos.solicitud_edicion_flujo import SolicitudEdicionFlujo
from app.modules.editor_flujo_ia.servicio.servicio_editor_flujo import ServicioEditorFlujoIa

router = APIRouter(prefix="/api/ia", tags=["ia"])


@router.post("/editar-flujo", response_model=RespuestaEdicionFlujo)
async def editar_flujo_con_ia(
    request: SolicitudEdicionFlujo = Body(
        ...,
        openapi_examples={
            "crear_loop": {
                "summary": "Crear loop entre actividades",
                "value": {
                    "workflow": {
                        "nodes": [
                            {"id": "inicio", "type": "start", "name": "Inicio"},
                            {"id": "revisar", "type": "task", "name": "Revisar solicitud"},
                            {"id": "solicitar", "type": "task", "name": "Solicitar datos"},
                            {"id": "fin", "type": "end", "name": "Fin"},
                        ],
                        "transitions": [
                            {"id": "tr_1", "from": "inicio", "to": "solicitar"},
                            {"id": "tr_2", "from": "solicitar", "to": "revisar"},
                            {"id": "tr_3", "from": "revisar", "to": "fin"},
                        ],
                        "forms": [],
                        "businessRules": [],
                    },
                    "prompt": "Crea un loop que vuelva desde Revisar solicitud hacia Solicitar datos.",
                },
            }
        },
    ),
    service: ServicioEditorFlujoIa = Depends(obtener_servicio_editor_flujo_ia),
) -> RespuestaEdicionFlujo:
    handler = getattr(service, "interpretar_edicion", None) or getattr(service, "edit_workflow")
    return await handler(request)


edit_workflow_with_ai = editar_flujo_con_ia

