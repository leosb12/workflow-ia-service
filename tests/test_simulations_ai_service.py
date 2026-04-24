import asyncio

from app.modules.simulations_ai.prompts.simulation_prompts import SimulationPrompts
from app.modules.simulations_ai.schemas.simulation_request import (
    SimulationAnalysisRequest,
    SimulationComparisonRequest,
)
from app.modules.simulations_ai.service.simulations_ai_service import SimulationsAiService


def build_analysis_request() -> SimulationAnalysisRequest:
    return SimulationAnalysisRequest.model_validate(
        {
            "policy": {
                "id": "policy-1",
                "nombre": "Politica A",
            },
            "configuration": {
                "instances": 100,
                "baseNodeDurationHours": 2.0,
                "variabilityPercent": 20.0,
                "includeAiAnalysis": True,
                "randomSeed": 42,
            },
            "result": {
                "instancesSimulated": 100,
                "totalEstimatedTimeHours": 430.5,
                "averageEstimatedTimeHours": 4.31,
                "highestLoadNodeId": "node-3",
                "highestLoadNodeName": "Revision documental",
                "highestLoadPercentage": 38.5,
                "bottleneckNodeIds": ["node-3", "node-5"],
                "bottleneckNodeNames": ["Revision documental", "Aprobacion final"],
                "nodeStats": [
                    {
                        "nodeId": "node-3",
                        "nodeName": "Revision documental",
                        "nodeType": "ACTIVIDAD",
                        "executions": 100,
                        "totalEstimatedTimeHours": 180.0,
                        "averageEstimatedTimeHours": 1.8,
                        "loadPercentage": 38.5,
                        "bottleneck": True,
                    }
                ],
                "decisionStats": [
                    {
                        "nodeId": "node-4",
                        "nodeName": "Validar monto",
                        "totalDecisions": 100,
                        "outcomes": {
                            "Aprobado (node-5)": 80,
                            "Observado (node-6)": 20,
                        },
                    }
                ],
                "warnings": [],
            },
            "actorId": "admin-1",
        }
    )


def build_comparison_request() -> SimulationComparisonRequest:
    return SimulationComparisonRequest.model_validate(
        {
            "firstPolicy": {"id": "policy-1", "nombre": "Politica A"},
            "secondPolicy": {"id": "policy-2", "nombre": "Politica B"},
            "configuration": {
                "instances": 100,
                "baseNodeDurationHours": 2.0,
                "variabilityPercent": 20.0,
                "includeAiAnalysis": True,
                "randomSeed": 42,
            },
            "comparison": {
                "firstAverageEstimatedTimeHours": 4.8,
                "secondAverageEstimatedTimeHours": 3.9,
                "firstBottleneckCount": 3,
                "secondBottleneckCount": 1,
                "averageTimeDifferenceHours": 0.9,
                "moreEfficientPolicyId": "policy-2",
                "moreEfficientPolicyName": "Politica B",
                "conclusion": "La Politica B muestra mejor desempeno general.",
            },
        }
    )


def test_simulation_analysis_builds_controlled_heuristic_response() -> None:
    service = SimulationsAiService(prompts=SimulationPrompts())

    response = asyncio.run(service.analyze(build_analysis_request()))

    assert response.available is True
    assert response.source == "AI"
    assert response.summary
    assert "1." in response.summary
    assert "2." in response.summary
    assert "puntaje" not in response.summary.lower()
    assert "revision documental" in response.summary.lower()
    assert "80%" in response.summary
    assert response.executive_conclusion
    assert "prioridades inmediatas" in response.executive_conclusion.lower()
    assert response.efficiency_score is not None
    assert any("carga" in issue.lower() for issue in response.detected_issues)
    assert response.bottlenecks


def test_simulation_comparison_returns_winner_and_recommendations() -> None:
    service = SimulationsAiService(prompts=SimulationPrompts())

    response = asyncio.run(service.compare(build_comparison_request()))

    assert response.available is True
    assert response.more_efficient_policy_id == "policy-2"
    assert response.more_efficient_policy_name == "Politica B"
    assert response.summary
    assert "1." in response.summary
    assert "lectura comparativa final" in response.summary.lower()
    assert "3.9 h" in response.summary.lower()
    assert "4.8 h" in response.summary.lower()
    assert "cuello(s) de botella" in response.summary.lower()
    assert "puntaje" not in response.summary.lower()
    assert response.executive_conclusion
    assert "decision definitiva" in response.executive_conclusion.lower()
    assert response.recommendations


def test_simulation_comparison_handles_missing_comparison_block() -> None:
    service = SimulationsAiService(prompts=SimulationPrompts())

    response = asyncio.run(service.compare(SimulationComparisonRequest.model_validate({})))

    assert response.available is True
    assert "suficientes metricas" in response.summary.lower()


def test_simulation_comparison_is_not_neutral_when_time_gap_is_huge() -> None:
    service = SimulationsAiService(prompts=SimulationPrompts())
    request = SimulationComparisonRequest.model_validate(
        {
            "firstPolicy": {"id": "policy-1", "nombre": "politica con ia"},
            "secondPolicy": {"id": "policy-2", "nombre": "sex"},
            "comparison": {
                "firstAverageEstimatedTimeHours": 64.77,
                "secondAverageEstimatedTimeHours": 11.97,
                "firstBottleneckCount": 1,
                "secondBottleneckCount": 1,
                "averageTimeDifferenceHours": 52.8,
                "moreEfficientPolicyId": "policy-2",
                "moreEfficientPolicyName": "sex",
            },
        }
    )

    response = asyncio.run(service.compare(request))

    assert "muy parecidos" not in response.summary.lower()
    assert "52.8 h" in response.summary.lower()
    assert "11.97 h" in response.summary.lower()
    assert "duracion acumulada" in " ".join(response.detected_issues).lower()
    assert response.more_efficient_policy_name == "sex"
