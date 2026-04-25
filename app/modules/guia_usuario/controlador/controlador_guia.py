from fastapi import APIRouter, Body, Depends

from app.modules.guia_usuario.infraestructura.dependencias import (
    obtener_servicio_guia_administrador,
    obtener_servicio_guia_funcionario,
)
from app.modules.guia_usuario.comun.solicitud_guia import (
    SolicitudGuiaAdministrador,
    SolicitudGuiaFuncionario,
)
from app.modules.guia_usuario.comun.respuesta_guia import (
    RespuestaGuiaAdministrador,
    RespuestaGuiaFuncionario,
)
from app.modules.guia_usuario.administrador.servicio_guia_administrador import ServicioGuiaAdministrador
from app.modules.guia_usuario.funcionario.servicio_guia_funcionario import ServicioGuiaFuncionario

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

_EMPLOYEE_GUIDE_EXAMPLE = {
    "userId": "func-1",
    "userName": "Funcionario Operativo",
    "role": "EMPLOYEE",
    "screen": "TASK_FORM",
    "question": "Que lleno aqui?",
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
            {
                "condition": "Si marcas Sí",
                "nextNode": "Revision legal",
                "nextDepartment": "Legal",
            },
            {
                "condition": "Si marcas No",
                "nextNode": "Rechazo de solicitud",
                "nextDepartment": "Atencion al Cliente",
            },
        ],
        "dashboardSummary": {
            "pendingTasks": 3,
            "inProgressTasks": 1,
            "completedTasks": 4,
            "overdueTasks": 1,
        },
        "taskQueue": [
            {
                "taskId": "task-1",
                "taskName": "Evaluar viabilidad tecnica",
                "taskStatus": "OVERDUE",
                "priority": "HIGH",
                "ageHours": 56,
                "overdue": True,
                "policyName": "Instalacion de medidor",
            }
        ],
        "availableActions": [
            "START_TASK",
            "SAVE_FORM",
            "COMPLETE_TASK",
            "ASK_HELP",
            "FILL_FORM_WITH_AI",
        ],
    },
}


@router.post("/admin", response_model=RespuestaGuiaAdministrador)
async def guiar_administrador(
    request: SolicitudGuiaAdministrador = Body(
        ...,
        openapi_examples={"admin_guide": {"value": _ADMIN_GUIDE_EXAMPLE}},
    ),
    service: ServicioGuiaAdministrador = Depends(obtener_servicio_guia_administrador),
) -> RespuestaGuiaAdministrador:
    handler = getattr(service, "guiar_administrador", None) or getattr(service, "guide_admin")
    return await handler(request)


@router.post("/employee", response_model=RespuestaGuiaFuncionario)
async def guiar_funcionario(
    request: SolicitudGuiaFuncionario = Body(
        ...,
        openapi_examples={"employee_guide": {"value": _EMPLOYEE_GUIDE_EXAMPLE}},
    ),
    service: ServicioGuiaFuncionario = Depends(obtener_servicio_guia_funcionario),
) -> RespuestaGuiaFuncionario:
    handler = getattr(service, "guiar_funcionario", None) or getattr(service, "guide_employee")
    return await handler(request)


guide_admin = guiar_administrador
guide_employee = guiar_funcionario
