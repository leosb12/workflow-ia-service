from fastapi import APIRouter, Body, Depends

from app.modules.simulations_ai.infrastructure.dependencies import get_simulations_ai_service
from app.modules.simulations_ai.schemas.simulation_request import (
    SimulationAnalysisRequest,
    SimulationComparisonRequest,
)
from app.modules.simulations_ai.schemas.simulation_response import (
    SimulationAnalysisResponse,
    SimulationComparisonResponse,
)
from app.modules.simulations_ai.service.simulations_ai_service import SimulationsAiService

router = APIRouter(prefix="/api/ia/simulations", tags=["ia"])

_ANALYZE_EXAMPLE = {
    "policy": {
        "id": "policy-1",
        "nombre": "Política A",
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

_COMPARE_EXAMPLE = {
    "firstPolicy": {
        "id": "policy-1",
        "nombre": "Política A",
    },
    "secondPolicy": {
        "id": "policy-2",
        "nombre": "Política B",
    },
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


@router.post("/analyze", response_model=SimulationAnalysisResponse)
async def analyze_simulation(
    request: SimulationAnalysisRequest = Body(..., openapi_examples={"simulation": {"value": _ANALYZE_EXAMPLE}}),
    service: SimulationsAiService = Depends(get_simulations_ai_service),
) -> SimulationAnalysisResponse:
    return await service.analyze(request)


@router.post("/compare", response_model=SimulationComparisonResponse)
async def compare_simulations(
    request: SimulationComparisonRequest = Body(..., openapi_examples={"simulation": {"value": _COMPARE_EXAMPLE}}),
    service: SimulationsAiService = Depends(get_simulations_ai_service),
) -> SimulationComparisonResponse:
    return await service.compare(request)
