from fastapi.testclient import TestClient

from app.main import app
from app.modules.user_guide.infrastructure.dependencies import get_mobile_user_guide_service
from app.modules.user_guide.schemas.guide_response import MobileUserGuideResponse


class StubMobileUserGuideService:
    async def guide_mobile_user(self, request):
        return MobileUserGuideResponse(
            answer="Tu tramite sigue en revision tecnica.",
            steps=["Revisa observaciones", "Consulta el historial si necesitas detalle"],
            estadoExplicado="EN_PROCESO significa que tu tramite todavia esta siendo revisado.",
            progresoExplicado="Llevas 2 de 5 etapas completadas.",
            documentosFaltantes=[],
            proximosPasos=["Revision legal"],
            accionesSugeridas=[{"action": "VER_HISTORIAL", "label": "Ver historial del tramite"}],
            severity="INFO",
            intent="EXPLICAR_ESTADO_TRAMITE",
            source="AI",
            available=True,
        )


def test_mobile_user_guide_route_returns_contextual_json() -> None:
    app.dependency_overrides[get_mobile_user_guide_service] = lambda: StubMobileUserGuideService()
    client = TestClient(app)

    response = client.post(
        "/api/ia/guide/mobile-user",
        json={
            "userId": "usr-1",
            "role": "MOBILE_USER",
            "screen": "DETALLE_TRAMITE",
            "question": "En que estado esta mi tramite?",
            "context": {
                "tramiteId": "inst-1",
                "accionesDisponibles": ["VER_HISTORIAL"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Tu tramite sigue en revision tecnica."
    assert payload["accionesSugeridas"][0]["action"] == "VER_HISTORIAL"
    assert payload["intent"] == "EXPLICAR_ESTADO_TRAMITE"

    app.dependency_overrides.clear()
