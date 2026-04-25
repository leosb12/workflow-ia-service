from fastapi import APIRouter, Body, Depends

from app.modules.simulacion.infraestructura.dependencias import obtener_servicio_simulacion
from app.modules.simulacion.modelos.solicitud_simulacion import (
    SimulationAnalysisRequest,
    SimulationComparisonRequest,
)
from app.modules.simulacion.modelos.respuesta_simulacion import (
    SimulationAnalysisResponse,
    SimulationComparisonResponse,
)
from app.modules.simulacion.servicio.servicio_simulacion import ServicioSimulacion

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
async def analizar_simulacion(
    request: SimulationAnalysisRequest = Body(..., openapi_examples={"simulation": {"value": _ANALYZE_EXAMPLE}}),
    service: ServicioSimulacion = Depends(obtener_servicio_simulacion),
) -> SimulationAnalysisResponse:
    handler = getattr(service, "analizar", None) or getattr(service, "analyze")
    return await handler(request)


@router.post("/compare", response_model=SimulationComparisonResponse)
async def comparar_simulaciones(
    request: SimulationComparisonRequest = Body(..., openapi_examples={"simulation": {"value": _COMPARE_EXAMPLE}}),
    service: ServicioSimulacion = Depends(obtener_servicio_simulacion),
) -> SimulationComparisonResponse:
    handler = getattr(service, "comparar", None) or getattr(service, "compare")
    return await handler(request)


analyze_simulation = analizar_simulacion
compare_simulations = comparar_simulaciones
