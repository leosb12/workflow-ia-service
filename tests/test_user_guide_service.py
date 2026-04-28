import asyncio

from app.modules.user_guide.prompts.admin_guide_prompts import AdminGuidePrompts
from app.modules.user_guide.schemas.guide_request import AdminGuideRequest
from app.modules.user_guide.service.admin_guide_fallback_service import (
    AdminGuideFallbackService,
)
from app.modules.user_guide.service.admin_guide_intent_classifier import (
    AdminGuideIntentClassifier,
)
from app.modules.user_guide.service.admin_guide_service import AdminGuideService
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        raise RuntimeError("LLM unavailable")


class StubPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        return """
        {
          "answer": "Estas en el disenador de politicas. Primero agrega nodos clave y luego valida responsables.",
          "steps": ["Agregar nodo inicial", "Agregar actividades principales", "Guardar politica"],
          "suggestedResponsible": {"name": "Departamento Tecnico", "reason": "Valida viabilidad tecnica."},
          "suggestedForm": [
            {"label": "Es viable tecnicamente?", "type": "BOOLEAN", "required": true}
          ],
          "detectedIssues": [
            {"type": "MISSING_END_NODE", "message": "La politica no tiene nodo final."}
          ],
          "suggestedActions": [
            {"action": "ADD_END_NODE", "label": "Agregar nodo final"}
          ],
          "severity": "WARNING",
          "intent": "SUGGEST_ACTIVITY_FORM",
          "source": "AI",
          "available": true
        }
        """


def build_request(question: str) -> AdminGuideRequest:
    return AdminGuideRequest.model_validate(
        {
            "userId": "admin-1",
            "userName": "Admin Principal",
            "role": "ADMIN",
            "screen": "POLICY_DESIGNER",
            "question": question,
            "context": {
                "policyId": "pol-1",
                "policyName": "Instalacion de medidor",
                "policyStatus": "BORRADOR",
                "selectedNode": {
                    "id": "node-1",
                    "type": "ACTIVITY",
                    "name": "Evaluar viabilidad tecnica",
                    "department": "Departamento Tecnico",
                    "formFields": [],
                    "incomingNodes": ["Inicio"],
                    "outgoingNodes": ["Decision tecnica"],
                },
                "policySummary": {
                    "hasStartNode": True,
                    "hasEndNode": False,
                    "totalActivities": 5,
                    "totalDecisions": 1,
                    "activitiesWithoutResponsible": 2,
                    "activitiesWithoutForm": 3,
                    "invalidConnections": 1,
                    "decisionsWithoutRoutes": 1,
                },
                "availableActions": [
                    "ADD_ACTIVITY",
                    "ADD_FORM_FIELD",
                    "ASSIGN_RESPONSIBLE",
                    "CONNECT_NODES",
                    "SAVE_POLICY",
                    "ACTIVATE_POLICY",
                ],
            },
        }
    )


def test_admin_guide_uses_fallback_when_llm_fails() -> None:
    service = AdminGuideService(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=AdminGuidePrompts(),
        classifier=AdminGuideIntentClassifier(),
        fallback_service=AdminGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_admin(build_request("Puedo activar esta politica?")))

    assert response.available is True
    assert response.source == "AI"
    assert response.severity == "ERROR"
    assert any(issue.type == "MISSING_END_NODE" for issue in response.detected_issues)
    assert any(action.action == "ADD_END_NODE" for action in response.suggested_actions)


def test_admin_guide_sanitizes_ai_response() -> None:
    service = AdminGuideService(
        prompt_runner=StubPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=AdminGuidePrompts(),
        classifier=AdminGuideIntentClassifier(),
        fallback_service=AdminGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_admin(build_request("Sugerime formulario")))

    assert response.source == "AI"
    assert response.intent == "SUGGEST_ACTIVITY_FORM"
    assert response.suggested_form
    assert response.suggested_form[0].type == "BOOLEAN"
    assert response.detected_issues[0].type == "MISSING_END_NODE"


def test_admin_guide_profile_answers_password_change_question() -> None:
    service = AdminGuideService(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=AdminGuidePrompts(),
        classifier=AdminGuideIntentClassifier(),
        fallback_service=AdminGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    request = AdminGuideRequest.model_validate(
        {
            "userId": "admin-1",
            "userName": "Admin Principal",
            "role": "ADMIN",
            "screen": "PERFIL_USUARIO",
            "question": "Donde cambio mi contrasena?",
            "context": {},
        }
    )

    response = asyncio.run(service.guide_admin(request))

    assert response.source == "AI"
    assert "perfil" in response.answer.lower()
    assert any("seguridad" in step.lower() for step in response.steps)


def test_admin_guide_profile_uses_heuristic_even_if_llm_is_available() -> None:
    service = AdminGuideService(
        prompt_runner=StubPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=AdminGuidePrompts(),
        classifier=AdminGuideIntentClassifier(),
        fallback_service=AdminGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    request = AdminGuideRequest.model_validate(
        {
            "userId": "admin-1",
            "userName": "Admin Principal",
            "role": "ADMIN",
            "screen": "PERFIL_USUARIO",
            "question": "Donde estoy?",
            "context": {},
        }
    )

    response = asyncio.run(service.guide_admin(request))

    assert response.source == "AI"
    assert "perfil" in response.answer.lower()
