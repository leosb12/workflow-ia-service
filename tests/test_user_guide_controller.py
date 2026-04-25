from fastapi.testclient import TestClient

from app.main import app
from app.modules.user_guide.infrastructure.dependencies import get_admin_guide_service
from app.modules.user_guide.schemas.guide_response import AdminGuideResponse


class StubAdminGuideService:
    async def guide_admin(self, request):
        return AdminGuideResponse(
            answer="Estas en el disenador de politicas.",
            steps=["Agrega nodos principales", "Configura responsables", "Valida activacion"],
            suggestedActions=[{"action": "SAVE_POLICY", "label": "Guardar politica"}],
            severity="INFO",
            intent="EXPLAIN_SCREEN",
            source="AI",
            available=True,
        )


def test_admin_guide_route_returns_contextual_json() -> None:
    app.dependency_overrides[get_admin_guide_service] = lambda: StubAdminGuideService()
    client = TestClient(app)

    response = client.post(
        "/api/ia/guide/admin",
        json={
            "userId": "admin-1",
            "role": "ADMIN",
            "screen": "POLICY_DESIGNER",
            "question": "Que hago aqui?",
            "context": {
                "policyId": "pol-1",
                "availableActions": ["SAVE_POLICY"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Estas en el disenador de politicas."
    assert payload["suggestedActions"][0]["action"] == "SAVE_POLICY"
    assert payload["intent"] == "EXPLAIN_SCREEN"

    app.dependency_overrides.clear()
