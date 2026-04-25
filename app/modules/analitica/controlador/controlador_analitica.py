from fastapi import APIRouter, Body, Depends

from app.modules.analitica.infraestructura.dependencias import obtener_servicio_analitica
from app.modules.analitica.modelos.solicitud_analitica import (
    DashboardAnalyticsRequest,
    PolicyImprovementRequest,
)
from app.modules.analitica.modelos.respuesta_analitica import (
    BottleneckAnalysisResponse,
    IntelligentSummaryResponse,
    PolicyImprovementResponse,
    TaskRedistributionResponse,
)
from app.modules.analitica.servicio.servicio_analitica import ServicioAnalitica

router = APIRouter(prefix="/api/ia/analytics", tags=["ia"])

_DASHBOARD_EXAMPLE = {
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


@router.post("/bottlenecks", response_model=BottleneckAnalysisResponse)
async def analizar_cuellos_botella(
    request: DashboardAnalyticsRequest = Body(..., openapi_examples={"dashboard": {"value": _DASHBOARD_EXAMPLE}}),
    service: ServicioAnalitica = Depends(obtener_servicio_analitica),
) -> BottleneckAnalysisResponse:
    return await service.analyze_bottlenecks(request)


@router.post("/task-redistribution", response_model=TaskRedistributionResponse)
async def recomendar_redistribucion_tareas(
    request: DashboardAnalyticsRequest = Body(..., openapi_examples={"dashboard": {"value": _DASHBOARD_EXAMPLE}}),
    service: ServicioAnalitica = Depends(obtener_servicio_analitica),
) -> TaskRedistributionResponse:
    return await service.recommend_task_redistribution(request)


@router.post("/policy-improvement", response_model=PolicyImprovementResponse)
async def mejorar_politica(
    request: PolicyImprovementRequest = Body(
        ...,
        openapi_examples={
            "policy_dashboard": {
                "value": {
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
                    "dashboard": _DASHBOARD_EXAMPLE,
                }
            }
        },
    ),
    service: ServicioAnalitica = Depends(obtener_servicio_analitica),
) -> PolicyImprovementResponse:
    return await service.improve_policy(request)


@router.post("/intelligent-summary", response_model=IntelligentSummaryResponse)
async def construir_resumen_inteligente(
    request: DashboardAnalyticsRequest = Body(..., openapi_examples={"dashboard": {"value": _DASHBOARD_EXAMPLE}}),
    service: ServicioAnalitica = Depends(obtener_servicio_analitica),
) -> IntelligentSummaryResponse:
    return await service.build_intelligent_summary(request)


analyze_bottlenecks = analizar_cuellos_botella
recommend_task_redistribution = recomendar_redistribucion_tareas
improve_policy = mejorar_politica
build_intelligent_summary = construir_resumen_inteligente
