from fastapi.testclient import TestClient

from app.main import app
from app.modules.user_guide.infrastructure.dependencies import get_employee_guide_service
from app.modules.user_guide.schemas.guide_response import EmployeeGuideResponse


class StubEmployeeGuideService:
    async def guide_employee(self, request):
        return EmployeeGuideResponse(
            answer="Debes completar el formulario actual y luego finalizar la tarea.",
            steps=["Completa los campos obligatorios", "Finaliza la tarea"],
            formHelp=[{"field": "viable", "help": "Marca Sí si es técnicamente viable."}],
            missingFields=[{"field": "viable", "message": "Debes indicar si es viable."}],
            nextStepExplanation="Si marcas Sí, pasará a Revisión Legal.",
            suggestedActions=[
                {"action": "COMPLETE_REQUIRED_FIELDS", "label": "Completar campos obligatorios"}
            ],
            severity="ERROR",
            intent="VALIDATE_BEFORE_COMPLETE",
            source="AI",
            available=True,
        )


def test_employee_guide_route_returns_contextual_json() -> None:
    app.dependency_overrides[get_employee_guide_service] = lambda: StubEmployeeGuideService()
    client = TestClient(app)

    response = client.post(
        "/api/ia/guide/employee",
        json={
            "userId": "func-1",
            "role": "EMPLOYEE",
            "screen": "TASK_FORM",
            "question": "Que me falta para finalizar?",
            "context": {
                "taskId": "task-1",
                "availableActions": ["COMPLETE_TASK"],
            },
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["answer"] == "Debes completar el formulario actual y luego finalizar la tarea."
    assert payload["missingFields"][0]["field"] == "viable"
    assert payload["intent"] == "VALIDATE_BEFORE_COMPLETE"

    app.dependency_overrides.clear()
