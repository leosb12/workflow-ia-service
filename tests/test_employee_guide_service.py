import asyncio

from app.modules.user_guide.prompts.employee_guide_prompts import EmployeeGuidePrompts
from app.modules.user_guide.schemas.guide_request import EmployeeGuideRequest
from app.modules.user_guide.service.employee_guide_fallback_service import (
    EmployeeGuideFallbackService,
)
from app.modules.user_guide.service.employee_guide_intent_classifier import (
    EmployeeGuideIntentClassifier,
)
from app.modules.user_guide.service.employee_guide_service import EmployeeGuideService
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        raise RuntimeError("LLM unavailable")


class StubPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        return """
        {
          "answer": "Debes completar primero el campo viable y luego revisar las observaciones.",
          "steps": ["Completa viable", "Revisa observaciones"],
          "formHelp": [
            {"field": "viable", "help": "Marca Sí si la instalación es técnicamente posible."}
          ],
          "missingFields": [
            {"field": "viable", "message": "Debes indicar si es viable antes de finalizar."}
          ],
          "prioritySuggestion": {
            "recommendedTaskId": "task-1",
            "reason": "Esta tarea está atrasada."
          },
          "nextStepExplanation": "Si marcas Sí, el trámite pasará a Revisión Legal.",
          "suggestedActions": [
            {"action": "COMPLETE_REQUIRED_FIELDS", "label": "Completar campos obligatorios"}
          ],
          "severity": "ERROR",
          "intent": "VALIDATE_BEFORE_COMPLETE",
          "source": "AI",
          "available": true
        }
        """


def build_request(question: str) -> EmployeeGuideRequest:
    return EmployeeGuideRequest.model_validate(
        {
            "userId": "func-1",
            "userName": "Funcionario Operativo",
            "role": "EMPLOYEE",
            "screen": "TASK_FORM",
            "question": question,
            "context": {
                "taskId": "task-1",
                "instanceId": "inst-1",
                "policyId": "pol-1",
                "policyName": "Instalacion de medidor",
                "currentNode": {
                    "id": "node-1",
                    "type": "ACTIVITY",
                    "name": "Evaluar viabilidad tecnica",
                    "description": "Validar si tecnicamente se puede instalar el medidor",
                    "department": "Departamento Tecnico",
                    "estimatedTime": "48h",
                },
                "taskStatus": "IN_PROGRESS",
                "priority": "HIGH",
                "form": {
                    "fields": [
                        {
                            "name": "viable",
                            "label": "Es viable tecnicamente?",
                            "type": "BOOLEAN",
                            "required": True,
                            "value": None,
                        },
                        {
                            "name": "observaciones",
                            "label": "Observaciones tecnicas",
                            "type": "TEXTAREA",
                            "required": False,
                            "value": "",
                        },
                    ],
                    "missingRequiredFields": ["viable"],
                },
                "historySummary": {
                    "completedSteps": 2,
                    "currentStep": "Evaluar viabilidad tecnica",
                    "pendingSteps": 3,
                    "lastCompletedBy": "Atencion al Cliente",
                },
                "nextPossibleSteps": [
                    {"condition": "Si marcas Sí", "nextNode": "Revision legal", "nextDepartment": "Legal"}
                ],
                "availableActions": ["START_TASK", "SAVE_FORM", "COMPLETE_TASK", "ASK_HELP"],
            },
        }
    )


def test_employee_guide_uses_fallback_when_llm_fails() -> None:
    service = EmployeeGuideService(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=EmployeeGuidePrompts(),
        classifier=EmployeeGuideIntentClassifier(),
        fallback_service=EmployeeGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_employee(build_request("Que me falta para finalizar?")))

    assert response.available is True
    assert response.source == "HEURISTIC"
    assert response.severity == "ERROR"
    assert response.missing_fields
    assert response.missing_fields[0].field == "viable"


def test_employee_guide_sanitizes_ai_response() -> None:
    service = EmployeeGuideService(
        prompt_runner=StubPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=EmployeeGuidePrompts(),
        classifier=EmployeeGuideIntentClassifier(),
        fallback_service=EmployeeGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_employee(build_request("Por que no puedo finalizar?")))

    assert response.source == "AI"
    assert response.intent == "VALIDATE_BEFORE_COMPLETE"
    assert response.form_help
    assert response.missing_fields
    assert response.priority_suggestion is not None
