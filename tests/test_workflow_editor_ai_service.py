import asyncio

from app.modules.editor_flujo_ia.dominio.validador_edicion_flujo import ValidadorEdicionFlujo
from app.modules.editor_flujo_ia.modelos.solicitud_edicion_flujo import SolicitudEdicionFlujo
from app.modules.editor_flujo_ia.prompts.prompts_editor_flujo import PromptsEditorFlujoIa
from app.modules.editor_flujo_ia.servicio.servicio_editor_flujo import ServicioEditorFlujoIa
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        raise RuntimeError("provider unavailable")


class StaticPromptRunner:
    def __init__(self, payload: str) -> None:
        self.payload = payload

    async def run_json_prompt(self, *, system_prompt: str, user_prompt: str) -> str:
        return self.payload


def build_workflow() -> dict:
    return {
        "nodes": [
            {"id": "inicio", "type": "start", "name": "Inicio", "description": "Inicio"},
            {"id": "solicitar", "type": "task", "name": "Solicitar datos", "description": "Solicita datos"},
            {"id": "revisar", "type": "task", "name": "Revisar solicitud", "description": "Revisa solicitud"},
            {"id": "validar", "type": "task", "name": "Validar documentos", "description": "Valida documentos"},
            {"id": "aprobar", "type": "task", "name": "Aprobar solicitud", "description": "Aprueba solicitud"},
            {"id": "notificar", "type": "task", "name": "Notificar resultado", "description": "Notifica resultado"},
            {"id": "fin", "type": "end", "name": "Fin", "description": "Fin"},
        ],
        "transitions": [
            {"id": "tr_inicio_solicitar", "from": "inicio", "to": "solicitar"},
            {"id": "tr_solicitar_revisar", "from": "solicitar", "to": "revisar"},
            {"id": "tr_revisar_validar", "from": "revisar", "to": "validar"},
            {"id": "tr_validar_aprobar", "from": "validar", "to": "aprobar"},
            {"id": "tr_aprobar_fin", "from": "aprobar", "to": "fin"},
        ],
        "forms": [
            {
                "id": "form_revisar",
                "nodeId": "revisar",
                "name": "Formulario de revision",
                "fields": [{"id": "observacion", "label": "Observacion", "type": "textarea", "required": False}],
            }
        ],
        "businessRules": [],
    }


def build_backend_workflow() -> dict:
    return {
        "nodos": [
            {"id": "inicio", "tipo": "INICIO", "nombre": "Inicio"},
            {"id": "solicitar", "tipo": "ACTIVIDAD", "nombre": "Solicitar datos del paciente"},
            {"id": "validar", "tipo": "ACTIVIDAD", "nombre": "Validar datos"},
            {"id": "fin", "tipo": "FIN", "nombre": "Fin"},
        ],
        "conexiones": [
            {"origen": "inicio", "destino": "solicitar"},
            {"origen": "solicitar", "destino": "validar"},
            {"origen": "validar", "destino": "fin"},
        ],
    }


def build_service() -> ServicioEditorFlujoIa:
    return ServicioEditorFlujoIa(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=PromptsEditorFlujoIa(),
        validator=ValidadorEdicionFlujo(),
    )


def build_service_with_runner(prompt_runner) -> ServicioEditorFlujoIa:
    return ServicioEditorFlujoIa(
        prompt_runner=prompt_runner,
        json_parser=JsonObjectParser(),
        prompts=PromptsEditorFlujoIa(),
        validator=ValidadorEdicionFlujo(),
    )


def run_prompt(prompt: str):
    request = SolicitudEdicionFlujo.model_validate({"workflow": build_workflow(), "prompt": prompt})
    return asyncio.run(build_service().interpretar_edicion(request))


def run_prompt_with_runner(prompt: str, prompt_runner):
    request = SolicitudEdicionFlujo.model_validate({"workflow": build_workflow(), "prompt": prompt})
    return asyncio.run(build_service_with_runner(prompt_runner).interpretar_edicion(request))


def run_backend_workflow_prompt(prompt: str):
    request = SolicitudEdicionFlujo.model_validate({"workflow": build_backend_workflow(), "prompt": prompt})
    return asyncio.run(build_service().interpretar_edicion(request))


def run_prompt_with_context(prompt: str, context: dict):
    request = SolicitudEdicionFlujo.model_validate({"workflow": build_workflow(), "prompt": prompt, "context": context})
    return asyncio.run(build_service().interpretar_edicion(request))


def test_delete_existing_activity_returns_delete_node_operation() -> None:
    response = run_prompt("Elimina la actividad Solicitar datos")

    assert response.success is True
    assert response.operations[0].type == "DELETE_NODE"
    assert response.operations[0].node_name == "Solicitar datos"
    assert response.requires_confirmation is True


def test_rename_activity_returns_rename_node_operation() -> None:
    response = run_prompt("Cambia el nombre de la actividad Solicitar datos a Solicitar informacion adicional")

    assert response.success is True
    assert response.operations[0].type == "RENAME_NODE"
    assert response.operations[0].node_name == "Solicitar datos"
    assert response.operations[0].new_name == "Solicitar informacion adicional"


def test_add_transition_returns_structured_transition_operation() -> None:
    response = run_prompt("Conecta Aprobar solicitud con Notificar resultado")

    assert response.success is True
    assert response.operations[0].type == "ADD_TRANSITION"
    assert response.operations[0].from_node_name == "Aprobar solicitud"
    assert response.operations[0].to_node_name == "Notificar resultado"


def test_create_loop_returns_explicit_loop_operation() -> None:
    response = run_prompt("Crea un loop que vuelva desde Revisar solicitud hacia Solicitar datos")

    assert response.success is True
    assert response.operations[0].type == "CREATE_LOOP"
    assert response.operations[0].from_node_name == "Revisar solicitud"
    assert response.operations[0].to_node_name == "Solicitar datos"
    assert response.operations[0].condition


def test_assign_initiator_as_responsible() -> None:
    response = run_prompt("Asigna como responsable de Solicitar datos a quien inicio el tramite")

    assert response.success is True
    assert response.operations[0].type == "ASSIGN_RESPONSIBLE"
    assert response.operations[0].responsible_type == "initiator"


def test_rejects_delete_start_node() -> None:
    response = run_prompt("Elimina Inicio")

    assert response.success is False
    assert response.operations[0].type == "DELETE_NODE"
    assert any("INICIO" in error for error in response.errors)


def test_ambiguous_prompt_requires_clarification() -> None:
    response = run_prompt("Mejora el flujo")

    assert response.success is False
    assert response.intent == "NEEDS_CLARIFICATION"
    assert response.operations == []
    assert response.warnings


def test_unknown_node_returns_validation_error() -> None:
    response = run_prompt("Elimina la actividad Nodo fantasma")

    assert response.success is False
    assert response.operations[0].type == "DELETE_NODE"
    assert any("inexistente" in error.lower() for error in response.errors)


def test_insert_activity_between_existing_nodes_returns_structured_operations() -> None:
    response = run_prompt(
        "Agregar un nodo de actividad 'Pedir foto' entre 'Solicitar datos' y 'Revisar solicitud'"
    )

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert [operation.type for operation in response.operations] == [
        "ADD_NODE",
        "DELETE_TRANSITION",
        "ADD_TRANSITION",
        "ADD_TRANSITION",
    ]
    assert response.operations[0].node_name == "Pedir foto"
    assert response.operations[1].from_node_name == "Solicitar datos"
    assert response.operations[1].to_node_name == "Revisar solicitud"
    assert response.operations[2].to_node_name == "Pedir foto"
    assert response.operations[3].from_node_name == "Pedir foto"


def test_invalid_ai_operations_fall_back_to_safe_local_interpretation() -> None:
    response = run_prompt_with_runner(
        "Agregar un nodo de actividad 'Pedir foto' entre 'Solicitar datos' y 'Revisar solicitud'",
        StaticPromptRunner(
            """
            {
              "success": true,
              "intent": "UPDATE_WORKFLOW",
              "summary": "La IA propuso una modificacion sobre el workflow.",
              "operations": [
                {"type": "ADD_NODE", "nodeName": "Solicitar datos", "nodeType": "task"},
                {"type": "ADD_TRANSITION", "fromNodeName": "Solicitar datos", "toNodeName": "Pedir foto"},
                {"type": "ADD_TRANSITION", "fromNodeName": "Pedir foto", "toNodeName": "Revisar solicitud"}
              ],
              "warnings": [],
              "requiresConfirmation": true
            }
            """
        ),
    )

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert any("interpretacion local segura" in warning for warning in response.warnings)
    assert [operation.type for operation in response.operations] == [
        "ADD_NODE",
        "DELETE_TRANSITION",
        "ADD_TRANSITION",
        "ADD_TRANSITION",
    ]


def test_backend_workflow_shape_supports_natural_add_activity_after_prompt() -> None:
    response = run_backend_workflow_prompt(
        "añadime una actividad para pedir foto al usuario despues de solicitar datos del apacienter"
    )

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert response.errors == []
    assert response.operations[0].type == "ADD_NODE"
    assert response.operations[0].node_name == "Pedir foto del paciente"
    assert response.operations[0].reference_node_name == "Solicitar datos del paciente"


def test_backend_workflow_shape_infers_position_for_short_add_node_prompt() -> None:
    response = run_backend_workflow_prompt("añadime el nodo pedir foto")

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert response.errors == []
    assert response.operations[0].type == "ADD_NODE"
    assert response.operations[0].node_name == "Pedir foto"
    assert response.operations[0].reference_node_name == "Solicitar datos del paciente"


def test_invalid_ai_add_node_without_node_name_falls_back_for_backend_workflow_shape() -> None:
    request = SolicitudEdicionFlujo.model_validate(
        {
            "workflow": build_backend_workflow(),
            "prompt": "añadime una actividad para pedir foto al usuario despues de solicitar datos del apacienter",
        }
    )
    response = asyncio.run(
        build_service_with_runner(
            StaticPromptRunner(
                """
                {
                  "success": true,
                  "intent": "UPDATE_WORKFLOW",
                  "summary": "Agregar actividad 'Pedir foto del paciente' despues de 'Solicitar datos del paciente'.",
                  "operations": [
                    {"type": "ADD_NODE", "nodeType": "task"},
                    {"type": "ADD_TRANSITION", "fromNodeName": "Solicitar datos del paciente", "toNodeName": "Pedir foto del paciente"},
                    {"type": "ADD_TRANSITION", "fromNodeName": "Pedir foto del paciente", "toNodeName": "Validar datos"},
                    {"type": "DELETE_TRANSITION", "fromNodeName": "Solicitar datos del paciente", "toNodeName": "Validar datos"}
                  ],
                  "warnings": [],
                  "requiresConfirmation": true
                }
                """
            )
        ).interpretar_edicion(request)
    )

    assert response.success is True
    assert response.errors == []
    assert response.operations[0].type == "ADD_NODE"
    assert response.operations[0].node_name == "Pedir foto del paciente"


def test_add_decision_uses_selected_node_context_for_relative_instruction() -> None:
    response = run_prompt_with_context(
        "anadime nodo decision preguntar si es hombre o mujer",
        {
            "selectedNode": {
                "id": "revisar",
                "name": "Revisar solicitud",
            }
        },
    )

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert response.errors == []
    assert response.operations[0].type == "ADD_NODE"
    assert response.operations[0].node_type == "decision"
    assert response.operations[0].node_name == "Preguntar si es hombre o mujer"
    assert response.operations[0].reference_node_name == "Revisar solicitud"
    assert response.operations[0].position == "after"


def test_reconnect_transition_uses_selected_and_target_node_context() -> None:
    response = run_prompt_with_context(
        "cambiame la conexion entre este nodo y conectalo al otro nodo",
        {
            "selectedNode": {
                "id": "validar",
                "name": "Validar documentos",
            },
            "targetNode": {
                "id": "notificar",
                "name": "Notificar resultado",
            },
        },
    )

    assert response.success is True
    assert response.intent == "UPDATE_WORKFLOW"
    assert response.errors == []
    assert [operation.type for operation in response.operations] == [
        "DELETE_TRANSITION",
        "ADD_TRANSITION",
    ]
    assert response.operations[0].from_node_name == "Validar documentos"
    assert response.operations[0].to_node_name == "Aprobar solicitud"
    assert response.operations[1].from_node_name == "Validar documentos"
    assert response.operations[1].to_node_name == "Notificar resultado"
