import copy

import pytest

from app.core.exceptions import ApiException
from app.ia.util.workflow_validator import WorkflowJsonValidator


def valid_workflow() -> dict:
    return {
        "policy": {
            "name": "Solicitud de credito",
            "description": "Flujo de revision y aprobacion",
            "objective": "Aprobar o rechazar solicitudes",
            "version": "1.0",
        },
        "roles": [
            {
                "id": "role_solicitante",
                "name": "Solicitante",
                "description": "Registra la solicitud",
            },
            {
                "id": "role_analista",
                "name": "Analista",
                "description": "Evalua la solicitud",
            },
        ],
        "nodes": [
            {
                "id": "start_1",
                "type": "start",
                "name": "Inicio",
                "description": "Inicio del tramite",
            },
            {
                "id": "task_registrar",
                "type": "task",
                "name": "Registrar solicitud",
                "description": "Capturar datos principales",
                "responsibleRoleId": "role_solicitante",
                "responsibleType": "department",
                "departmentHint": "Solicitante",
                "formId": "form_registro",
            },
            {
                "id": "decision_aprobacion",
                "type": "decision",
                "name": "Evaluar aprobacion",
                "description": "Determina si cumple criterios",
                "decisionCriteria": "Monto y capacidad de pago",
            },
            {
                "id": "end_aprobado",
                "type": "end",
                "name": "Aprobado",
                "description": "Solicitud aprobada",
            },
            {
                "id": "end_rechazado",
                "type": "end",
                "name": "Rechazado",
                "description": "Solicitud rechazada",
            },
        ],
        "transitions": [
            {
                "id": "tr_inicio_registro",
                "from": "start_1",
                "to": "task_registrar",
                "label": "Iniciar",
                "condition": None,
            },
            {
                "id": "tr_registro_decision",
                "from": "task_registrar",
                "to": "decision_aprobacion",
                "label": "Enviar",
                "condition": None,
            },
            {
                "id": "tr_aprobar",
                "from": "decision_aprobacion",
                "to": "end_aprobado",
                "label": "Aprobar",
                "condition": "Cumple criterios",
            },
            {
                "id": "tr_rechazar",
                "from": "decision_aprobacion",
                "to": "end_rechazado",
                "label": "Rechazar",
                "condition": "No cumple criterios",
            },
        ],
        "forms": [
            {
                "id": "form_registro",
                "nodeId": "task_registrar",
                "name": "Formulario de solicitud",
                "fields": [
                    {
                        "id": "field_monto",
                        "label": "Monto solicitado",
                        "type": "currency",
                        "required": True,
                        "options": [],
                    }
                ],
            }
        ],
        "businessRules": [
            {
                "id": "rule_capacidad_pago",
                "name": "Capacidad de pago",
                "description": "Valida capacidad de pago",
                "appliesToNodeId": "decision_aprobacion",
                "expression": "capacidad de pago suficiente",
                "severity": "blocking",
            }
        ],
        "analysis": {
            "summary": "Workflow basico de credito",
            "assumptions": [],
            "warnings": [],
            "complexity": "medium",
        },
    }


def test_validate_accepts_valid_workflow() -> None:
    WorkflowJsonValidator().validate(valid_workflow())


def test_validate_rejects_transition_to_missing_node() -> None:
    workflow = valid_workflow()
    workflow["transitions"][0]["to"] = "missing_node"

    with pytest.raises(ApiException) as exc:
        WorkflowJsonValidator().validate(workflow)

    assert "destino inexistente" in exc.value.message


def test_validate_rejects_decision_with_single_exit() -> None:
    workflow = valid_workflow()
    workflow["transitions"] = [
        transition
        for transition in workflow["transitions"]
        if transition["id"] != "tr_rechazar"
    ]

    with pytest.raises(ApiException) as exc:
        WorkflowJsonValidator().validate(workflow)

    assert "multiples salidas" in exc.value.message


def test_validate_rejects_task_without_responsible_role() -> None:
    workflow = copy.deepcopy(valid_workflow())
    del workflow["nodes"][1]["responsibleRoleId"]

    with pytest.raises(ApiException) as exc:
        WorkflowJsonValidator().validate(workflow)

    assert "responsibleRoleId" in exc.value.message
