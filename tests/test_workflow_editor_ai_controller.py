from fastapi.testclient import TestClient

from app.main import app
from app.modules.editor_flujo_ia.infraestructura.dependencias import obtener_servicio_editor_flujo_ia
from app.modules.editor_flujo_ia.modelos.respuesta_edicion_flujo import (
    OperacionEdicionFlujo,
    RespuestaEdicionFlujo,
)


class StubWorkflowEditorAiService:
    async def interpretar_edicion(self, request):
        return RespuestaEdicionFlujo(
            success=True,
            intent="UPDATE_WORKFLOW",
            summary="Se propone una transicion.",
            operations=[
                OperacionEdicionFlujo(
                    type="ADD_TRANSITION",
                    from_node_name="Revisar solicitud",
                    to_node_name="Solicitar datos",
                    condition="Informacion incompleta",
                )
            ],
            warnings=[],
            errors=[],
            requires_confirmation=True,
        )


def test_workflow_editor_ai_route_returns_preview_json() -> None:
    app.dependency_overrides[obtener_servicio_editor_flujo_ia] = lambda: StubWorkflowEditorAiService()
    client = TestClient(app)

    response = client.post(
        "/api/ia/editar-flujo",
        json={
            "workflow": {
                "nodes": [
                    {"id": "inicio", "type": "start", "name": "Inicio"},
                    {"id": "revisar", "type": "task", "name": "Revisar solicitud"},
                    {"id": "solicitar", "type": "task", "name": "Solicitar datos"},
                ],
                "transitions": [],
                "forms": [],
                "businessRules": [],
            },
            "prompt": "Crea un loop que vuelva desde Revisar solicitud hacia Solicitar datos",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert payload["requiresConfirmation"] is True
    assert payload["operations"][0]["type"] == "ADD_TRANSITION"

    app.dependency_overrides.clear()

