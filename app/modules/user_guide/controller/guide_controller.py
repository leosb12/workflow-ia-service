from fastapi import APIRouter, Body, Depends

from app.modules.user_guide.infrastructure.dependencies import get_admin_guide_service
from app.modules.user_guide.schemas.guide_request import AdminGuideRequest
from app.modules.user_guide.schemas.guide_response import AdminGuideResponse
from app.modules.user_guide.service.admin_guide_service import AdminGuideService

router = APIRouter(prefix="/api/ia/guide", tags=["ia"])

_ADMIN_GUIDE_EXAMPLE = {
    "userId": "admin-1",
    "userName": "Administrador Principal",
    "role": "ADMIN",
    "screen": "POLICY_DESIGNER",
    "question": "Que hago aqui?",
    "context": {
        "policyId": "pol-1",
        "policyName": "Instalacion de medidor",
        "policyStatus": "BORRADOR",
        "selectedNode": {
            "id": "node-1",
            "type": "ACTIVITY",
            "name": "Evaluar viabilidad tecnica",
            "department": "Departamento Tecnico",
            "responsible": None,
            "responsibleType": None,
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
            "parallelNodesIncomplete": 0,
            "orphanNodes": 0,
        },
        "detectedIssues": [
            {"type": "MISSING_END_NODE", "message": "La politica no tiene nodo final."}
        ],
        "availableActions": [
            "ADD_ACTIVITY",
            "ADD_DECISION",
            "ADD_FORM_FIELD",
            "ASSIGN_RESPONSIBLE",
            "CONNECT_NODES",
            "SAVE_POLICY",
            "ACTIVATE_POLICY",
        ],
        "policyDepartments": ["Departamento Tecnico", "Atencion al Cliente"],
    },
}


@router.post("/admin", response_model=AdminGuideResponse)
async def guide_admin(
    request: AdminGuideRequest = Body(
        ...,
        openapi_examples={"admin_guide": {"value": _ADMIN_GUIDE_EXAMPLE}},
    ),
    service: AdminGuideService = Depends(get_admin_guide_service),
) -> AdminGuideResponse:
    return await service.guide_admin(request)
