from fastapi.testclient import TestClient

from app.main import app
from app.modules.simulations_ai.infrastructure.dependencies import get_simulations_ai_service
from app.modules.simulations_ai.schemas.simulation_response import (
    SimulationAnalysisResponse,
    SimulationComparisonResponse,
)


class StubSimulationsAiService:
    async def analyze(self, request):
        return SimulationAnalysisResponse(
            summary="Resumen de simulacion.",
            source="AI",
            available=True,
            recommendations=["Revisar carga."],
            detectedIssues=["Carga concentrada."],
            strengths=["Distribucion aceptable."],
            risks=["Riesgo moderado."],
            bottlenecks=["Revision documental"],
            efficiencyScore=82.5,
            executiveConclusion="Conclusión de prueba.",
        )

    async def compare(self, request):
        return SimulationComparisonResponse(
            summary="Resumen de comparacion.",
            source="AI",
            available=True,
            recommendations=["Elegir la politica B."],
            detectedIssues=["Diferencia moderada."],
            strengths=["Menor tiempo promedio."],
            risks=["Sensibilidad a la semilla."],
            efficiencyScore=91.0,
            executiveConclusion="La politica B se ve mejor.",
            moreEfficientPolicyId="policy-2",
            moreEfficientPolicyName="Política B",
        )


def build_analysis_body() -> dict:
    return {
        "policy": {"id": "policy-1", "nombre": "Política A"},
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
            "highestLoadNodeName": "Revisión documental",
            "highestLoadPercentage": 38.5,
            "bottleneckNodeIds": ["node-3", "node-5"],
            "bottleneckNodeNames": ["Revisión documental", "Aprobación final"],
            "nodeStats": [
                {
                    "nodeId": "node-3",
                    "nodeName": "Revisión documental",
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


def build_comparison_body() -> dict:
    return {
        "firstPolicy": {"id": "policy-1", "nombre": "Política A"},
        "secondPolicy": {"id": "policy-2", "nombre": "Política B"},
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
            "moreEfficientPolicyName": "Política B",
            "conclusion": "La Política B muestra mejor desempeño general.",
        },
        "actorId": "admin-1",
    }


def test_simulations_routes_return_controlled_json() -> None:
    app.dependency_overrides[get_simulations_ai_service] = lambda: StubSimulationsAiService()
    client = TestClient(app)

    analyze = client.post("/api/ia/simulations/analyze", json=build_analysis_body())
    compare = client.post("/api/ia/simulations/compare", json=build_comparison_body())

    assert analyze.status_code == 200
    assert analyze.json()["available"] is True
    assert analyze.json()["source"] == "AI"
    assert compare.status_code == 200
    assert compare.json()["moreEfficientPolicyId"] == "policy-2"
    assert compare.json()["summary"] == "Resumen de comparacion."

    app.dependency_overrides.clear()
