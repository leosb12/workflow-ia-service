import asyncio

from app.modules.analytics_ai.prompts.analytics_prompts import AnalyticsPrompts
from app.modules.analytics_ai.schemas.analytics_request import (
    DashboardAnalyticsRequest,
    PolicyImprovementRequest,
)
from app.modules.analytics_ai.service.analytics_ai_service import AnalyticsAiService
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("provider unavailable")


class StaticPromptRunner:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        return self.payload


def build_dashboard_request() -> DashboardAnalyticsRequest:
    return DashboardAnalyticsRequest.model_validate(
        {
            "general": {
                "totalPolicies": 10,
                "activePolicies": 6,
                "totalInstances": 120,
                "inProgressInstances": 40,
                "completedInstances": 70,
                "rejectedInstances": 10,
                "pendingTasks": 25,
                "completedTasks": 180,
                "averageResolutionTimeHours": 18.5,
                "hasEnoughResolutionTimeData": True,
            },
            "attentionTimes": {
                "averageByPolicy": [
                    {
                        "policyId": "pol-1",
                        "policyName": "Solicitud de Credito",
                        "averageHours": 20.4,
                        "completedInstances": 15,
                    }
                ],
                "averageByNode": [
                    {
                        "nodeId": "node-1",
                        "nodeName": "Revision documental",
                        "averageHours": 8.2,
                        "completedTasks": 30,
                    }
                ],
                "averageByDepartment": [
                    {
                        "departmentId": "dep-1",
                        "departmentName": "Legal",
                        "averageHours": 12.5,
                        "completedTasks": 20,
                    }
                ],
                "averageByOfficial": [
                    {
                        "officialId": "user-1",
                        "officialName": "Juan Perez",
                        "averageHours": 6.3,
                        "completedTasks": 12,
                    },
                    {
                        "officialId": "user-2",
                        "officialName": "Ana Gomez",
                        "averageHours": 3.1,
                        "completedTasks": 20,
                    },
                ],
                "slowestActivity": {
                    "nodeId": "node-1",
                    "nodeName": "Revision documental",
                    "averageHours": 8.2,
                },
                "fastestActivity": {
                    "nodeId": "node-2",
                    "nodeName": "Registro inicial",
                    "averageHours": 1.4,
                },
                "hasEnoughData": True,
            },
            "taskAccumulation": {
                "pendingByOfficial": [
                    {
                        "officialId": "user-1",
                        "officialName": "Juan Perez",
                        "pendingTasks": 8,
                        "oldestTaskAgeHours": 36,
                    },
                    {
                        "officialId": "user-2",
                        "officialName": "Ana Gomez",
                        "pendingTasks": 2,
                        "oldestTaskAgeHours": 8,
                    },
                ],
                "pendingByDepartment": [
                    {
                        "departmentId": "dep-1",
                        "departmentName": "Legal",
                        "pendingTasks": 15,
                        "oldestTaskAgeHours": 48,
                    }
                ],
                "pendingByPolicy": [
                    {
                        "policyId": "pol-1",
                        "policyName": "Solicitud de Credito",
                        "pendingTasks": 10,
                        "oldestTaskAgeHours": 30,
                    }
                ],
                "pendingByNode": [
                    {
                        "nodeId": "node-1",
                        "nodeName": "Revision documental",
                        "pendingTasks": 7,
                        "oldestTaskAgeHours": 22,
                    }
                ],
                "oldestPendingTasks": [
                    {
                        "taskId": "task-1",
                        "policyName": "Solicitud de Credito",
                        "nodeName": "Revision documental",
                        "assignedToName": "Juan Perez",
                        "departmentName": "Legal",
                        "ageHours": 48,
                        "createdAt": "2026-04-23T10:00:00",
                    }
                ],
            },
        }
    )


def build_service(prompt_runner) -> AnalyticsAiService:
    return AnalyticsAiService(
        prompt_runner=prompt_runner,
        json_parser=JsonObjectParser(),
        prompts=AnalyticsPrompts(),
    )


def test_bottlenecks_filters_invented_entities_and_keeps_known_ones() -> None:
    service = build_service(
        StaticPromptRunner(
            """
            {
              "summary": "Revision documental concentra la mayor demora.",
              "bottlenecks": [
                {
                  "type": "NODE",
                  "name": "Revision documental",
                  "severity": "HIGH",
                  "evidence": "Es la actividad mas lenta y acumula pendientes.",
                  "impact": "Demora tramites.",
                  "recommendation": "Dividir la actividad."
                },
                {
                  "type": "OFFICIAL",
                  "name": "Funcionario Inventado",
                  "severity": "HIGH",
                  "evidence": "No valido.",
                  "impact": "No valido.",
                  "recommendation": "No valido."
                }
              ],
              "source": "AI",
              "available": true
            }
            """
        )
    )

    response = asyncio.run(service.analyze_bottlenecks(build_dashboard_request()))

    assert response.available is True
    assert len(response.bottlenecks) == 1
    assert response.bottlenecks[0].name == "Revision documental"


def test_task_redistribution_returns_unavailable_fallback_when_llm_fails() -> None:
    service = build_service(FailingPromptRunner())

    response = asyncio.run(service.recommend_task_redistribution(build_dashboard_request()))

    assert response.available is False
    assert response.recommendations == []
    assert "no esta disponible" in response.summary.lower()


def test_task_redistribution_rejects_invalid_receiver_with_higher_load() -> None:
    service = build_service(
        StaticPromptRunner(
            """
            {
              "summary": "Redistribucion sugerida.",
              "recommendations": [
                {
                  "fromOfficial": "Ana Gomez",
                  "toOfficial": "Juan Perez",
                  "reason": "Mover carga.",
                  "priority": "HIGH",
                  "expectedImpact": "Reducir acumulacion."
                },
                {
                  "fromOfficial": "Juan Perez",
                  "toOfficial": "Ana Gomez",
                  "reason": "Juan tiene mas pendientes y mayor antiguedad.",
                  "priority": "HIGH",
                  "expectedImpact": "Reducir acumulacion."
                }
              ],
              "source": "AI",
              "available": true
            }
            """
        )
    )

    response = asyncio.run(service.recommend_task_redistribution(build_dashboard_request()))

    assert len(response.recommendations) == 1
    assert response.recommendations[0].from_official == "Juan Perez"
    assert response.recommendations[0].to_official == "Ana Gomez"


def test_policy_improvement_uses_known_steps_only() -> None:
    request = PolicyImprovementRequest.model_validate(
        {
            "policyId": "pol-1",
            "policyName": "Solicitud de Credito",
            "workflowStructure": {
                "nodes": [
                    {"id": "node-1", "name": "Revision documental", "type": "task"},
                    {"id": "node-2", "name": "Registro inicial", "type": "task"},
                ],
                "transitions": [
                    {"id": "tr-1", "from": "node-2", "to": "node-1", "label": "Enviar a revision"}
                ],
            },
            "dashboard": build_dashboard_request().model_dump(by_alias=True),
        }
    )
    service = build_service(
        StaticPromptRunner(
            """
            {
              "summary": "Hay una mejora clara.",
              "policyIssues": [
                {
                  "nodeOrStep": "Revision documental",
                  "problem": "Concentra demoras.",
                  "evidence": "Es la actividad mas lenta.",
                  "recommendation": "Agregar una prevalidacion.",
                  "priority": "HIGH"
                },
                {
                  "nodeOrStep": "Nodo inventado",
                  "problem": "No valido.",
                  "evidence": "No valido.",
                  "recommendation": "No valido.",
                  "priority": "HIGH"
                }
              ],
              "source": "AI",
              "available": true
            }
            """
        )
    )

    response = asyncio.run(service.improve_policy(request))

    assert response.available is True
    assert len(response.policy_issues) == 1
    assert response.policy_issues[0].node_or_step == "Revision documental"
