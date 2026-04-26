from dataclasses import dataclass, field
from typing import Any
from difflib import SequenceMatcher
import unicodedata

from app.modules.editor_flujo_ia.modelos.respuesta_edicion_flujo import OperacionEdicionFlujo


@dataclass
class ResultadoValidacionEdicion:
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)

    @property
    def is_valid(self) -> bool:
        return not self.errors


class ValidadorEdicionFlujo:
    NODE_TYPES = {"start", "task", "decision", "parallel_start", "parallel_end", "end"}
    FIELD_TYPES = {"text", "textarea", "number", "date", "boolean", "select", "file", "email", "phone", "currency"}

    def validar(
        self,
        workflow: dict[str, Any],
        operations: list[OperacionEdicionFlujo],
    ) -> ResultadoValidacionEdicion:
        result = ResultadoValidacionEdicion()
        context = _WorkflowContext(workflow)

        if not context.nodes:
            result.errors.append("El workflow actual no contiene nodos para validar la edicion.")
            return result

        if not operations:
            result.warnings.append("No se detectaron operaciones de edicion aplicables.")
            return result

        added_nodes = self._collect_added_nodes(context, operations, result)
        planned_transitions: set[tuple[str, str]] = set()

        for operation in operations:
            self._validar_operacion(context, added_nodes, planned_transitions, operation, result)

        self._validar_riesgos_de_grafo(context, added_nodes, operations, result)
        result.errors = self._deduplicate(result.errors)
        result.warnings = self._deduplicate(result.warnings)
        return result

    def _collect_added_nodes(
        self,
        context: "_WorkflowContext",
        operations: list[OperacionEdicionFlujo],
        result: ResultadoValidacionEdicion,
    ) -> dict[str, str]:
        added_nodes: dict[str, str] = {}
        for operation in operations:
            if operation.type != "ADD_NODE":
                continue

            if not operation.node_name:
                result.errors.append("ADD_NODE requiere nodeName para identificar el nuevo nodo.")
                continue

            node_key = self._normalize(operation.node_name)
            if context.find_node_id_by_name(operation.node_name):
                result.errors.append(f"ADD_NODE crearia un nodo duplicado: {operation.node_name}.")
                continue

            if node_key in added_nodes:
                result.errors.append(f"ADD_NODE esta duplicado para el nodo nuevo: {operation.node_name}.")
                continue

            added_nodes[node_key] = operation.node_id or f"new:{node_key}"

            if operation.node_type and operation.node_type not in self.NODE_TYPES:
                result.errors.append(f"ADD_NODE usa un tipo de nodo invalido: {operation.node_type}.")
            if not operation.node_type:
                result.warnings.append(f"ADD_NODE para {operation.node_name} no indica nodeType.")
            if operation.node_type == "task" and not (
                operation.responsible_role_id
                or operation.responsible_role_name
                or operation.responsible_type == "initiator"
                or operation.department_hint
            ):
                result.warnings.append(
                    f"El nuevo nodo task {operation.node_name} no define responsable; debe completarse antes de aplicar."
                )
        return added_nodes

    def _validar_operacion(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        planned_transitions: set[tuple[str, str]],
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        if operation.type == "ADD_NODE":
            self._validar_add_node(context, added_nodes, operation, result)
            return

        if operation.type in {"UPDATE_NODE", "MOVE_NODE"}:
            self._require_existing_node(context, operation.node_id, operation.node_name, operation.type, result)
            if operation.type == "MOVE_NODE" and (operation.reference_node_id or operation.reference_node_name):
                self._require_existing_node(
                    context,
                    operation.reference_node_id,
                    operation.reference_node_name,
                    "MOVE_NODE.reference",
                    result,
                )
            return

        if operation.type == "DELETE_NODE":
            self._validar_delete_node(context, operation, result)
            return

        if operation.type == "RENAME_NODE":
            self._validar_rename_node(context, operation, result)
            return

        if operation.type in {"ADD_TRANSITION", "CREATE_LOOP"}:
            self._validar_add_transition(context, added_nodes, planned_transitions, operation, result)
            return

        if operation.type == "DELETE_TRANSITION":
            self._validar_delete_transition(context, operation, result)
            return

        if operation.type == "UPDATE_TRANSITION":
            self._validar_update_transition(context, added_nodes, operation, result)
            return

        if operation.type == "ASSIGN_RESPONSIBLE":
            self._validar_responsable(context, operation, result)
            return

        if operation.type in {"UPDATE_FORM", "ADD_FORM_FIELD", "DELETE_FORM_FIELD"}:
            self._validar_formulario(context, operation, result)
            return

        if operation.type == "UPDATE_DECISION_CONDITION":
            self._validar_condicion_decision(context, operation, result)
            return

        if operation.type in {"ADD_BUSINESS_RULE", "DELETE_BUSINESS_RULE"}:
            self._validar_regla_negocio(context, operation, result)

    def _validar_add_node(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        if operation.reference_node_id or operation.reference_node_name:
            self._require_existing_node(
                context,
                operation.reference_node_id,
                operation.reference_node_name,
                "ADD_NODE.reference",
                result,
            )

        if operation.position and not (operation.reference_node_id or operation.reference_node_name):
            result.warnings.append("ADD_NODE indica position, pero no referenceNodeName/referenceNodeId.")

        node_key = self._normalize(operation.node_name or "")
        has_structural_link = bool(operation.reference_node_id or operation.reference_node_name)
        if node_key and not has_structural_link:
            has_transition_link = False
            for candidate in added_nodes:
                if candidate == node_key:
                    continue
            if not has_transition_link:
                result.warnings.append(
                    f"ADD_NODE para {operation.node_name} no incluye referencia estructural; podria quedar huerfano."
                )

    def _validar_delete_node(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        node = self._require_existing_node(context, operation.node_id, operation.node_name, "DELETE_NODE", result)
        if not node:
            return

        node_name = str(node.get("name") or operation.node_name or operation.node_id)
        node_type = str(node.get("type") or "").strip().lower()
        if node_type == "start" or self._normalize(node_name) == "inicio":
            result.errors.append("No se permite eliminar el nodo INICIO.")
            return

        if node_type == "end" and context.count_nodes_by_type("end") <= 1:
            result.errors.append("No se permite eliminar el unico nodo FIN del workflow.")

        connected = context.transitions_connected_to(str(node.get("id")))
        if connected:
            result.warnings.append(
                f"Eliminar {node_name} tambien impacta {len(connected)} transicion(es); debe previsualizarse antes de aplicar."
            )

    def _validar_rename_node(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        self._require_existing_node(context, operation.node_id, operation.node_name, "RENAME_NODE", result)
        if not operation.new_name:
            result.errors.append("RENAME_NODE requiere newName.")
            return
        existing_id = context.find_node_id_by_name(operation.new_name)
        current_id = operation.node_id or context.find_node_id_by_name(operation.node_name or "")
        if existing_id and existing_id != current_id:
            result.errors.append(f"RENAME_NODE usaria un nombre ya existente: {operation.new_name}.")

    def _validar_add_transition(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        planned_transitions: set[tuple[str, str]],
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        from_id = self._resolve_node_reference(
            context,
            added_nodes,
            operation.from_node_id,
            operation.from_node_name,
            "origen",
            operation.type,
            result,
        )
        to_id = self._resolve_node_reference(
            context,
            added_nodes,
            operation.to_node_id,
            operation.to_node_name,
            "destino",
            operation.type,
            result,
        )
        if not from_id or not to_id:
            return

        pair = (from_id, to_id)
        if context.has_transition(from_id, to_id):
            result.errors.append(
                f"{operation.type} crearia una transicion duplicada entre {operation.from_node_name or from_id} y {operation.to_node_name or to_id}."
            )
        if pair in planned_transitions:
            result.errors.append(
                f"La propuesta contiene transiciones duplicadas entre {operation.from_node_name or from_id} y {operation.to_node_name or to_id}."
            )
        planned_transitions.add(pair)

        from_type = context.node_type(from_id)
        if from_type == "decision" and not self._text(operation.condition):
            result.warnings.append("Una transicion que sale de una decision debe tener condition entendible.")

        if operation.type == "CREATE_LOOP" and not self._text(operation.condition):
            result.warnings.append("CREATE_LOOP debe incluir una condition explicita para confirmar que el ciclo es intencional.")

    def _validar_delete_transition(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        transition = context.find_transition(
            transition_id=operation.transition_id,
            from_id=operation.from_node_id,
            from_name=operation.from_node_name,
            to_id=operation.to_node_id,
            to_name=operation.to_node_name,
        )
        if transition is None:
            result.errors.append("DELETE_TRANSITION no encontro la transicion indicada en el workflow actual.")
            return

        from_id = str(transition.get("from") or "")
        if context.node_type(from_id) == "decision" and context.outgoing_count(from_id) <= 2:
            result.warnings.append("Eliminar esta transicion dejaria una decision con menos de dos salidas.")

    def _validar_update_transition(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        transition = context.find_transition(
            transition_id=operation.transition_id,
            from_id=operation.from_node_id,
            from_name=operation.from_node_name,
            to_id=operation.to_node_id,
            to_name=operation.to_node_name,
        )
        if transition is None:
            result.errors.append("UPDATE_TRANSITION no encontro la transicion indicada en el workflow actual.")
            return

        if operation.from_node_id or operation.from_node_name:
            self._resolve_node_reference(
                context,
                added_nodes,
                operation.from_node_id,
                operation.from_node_name,
                "origen",
                "UPDATE_TRANSITION",
                result,
            )
        if operation.to_node_id or operation.to_node_name:
            self._resolve_node_reference(
                context,
                added_nodes,
                operation.to_node_id,
                operation.to_node_name,
                "destino",
                "UPDATE_TRANSITION",
                result,
            )

    def _validar_responsable(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        node = self._require_existing_node(context, operation.node_id, operation.node_name, "ASSIGN_RESPONSIBLE", result)
        if not node:
            return
        if str(node.get("type") or "").strip().lower() != "task":
            result.errors.append("ASSIGN_RESPONSIBLE solo puede aplicarse a nodos task.")
        if operation.responsible_type == "initiator":
            return
        if not (
            operation.responsible_role_id
            or operation.responsible_role_name
            or operation.department_hint
        ):
            result.warnings.append("ASSIGN_RESPONSIBLE no indica responsableRoleId, responsibleRoleName ni departmentHint.")

    def _validar_formulario(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        node = None
        if operation.node_id or operation.node_name:
            node = self._require_existing_node(context, operation.node_id, operation.node_name, operation.type, result)
            if node and str(node.get("type") or "").strip().lower() != "task":
                result.errors.append(f"{operation.type} solo puede asociarse a nodos task.")

        if operation.type == "UPDATE_FORM":
            if not node and not operation.form_id:
                result.errors.append("UPDATE_FORM requiere nodeName/nodeId o formId.")
            return

        if operation.type == "ADD_FORM_FIELD":
            if not node and not operation.form_id:
                result.errors.append("ADD_FORM_FIELD requiere nodeName/nodeId o formId.")
            if operation.field_type and operation.field_type not in self.FIELD_TYPES:
                result.errors.append(f"ADD_FORM_FIELD usa un tipo de campo invalido: {operation.field_type}.")
            if not operation.field_label:
                result.warnings.append("ADD_FORM_FIELD no indica fieldLabel.")
            if not operation.field_type:
                result.warnings.append("ADD_FORM_FIELD no indica fieldType.")
            return

        form = context.find_form(operation.form_id, operation.node_id, operation.node_name)
        if form is None:
            result.errors.append("DELETE_FORM_FIELD no encontro el formulario indicado.")
            return

        if not operation.field_id and not operation.field_label:
            result.errors.append("DELETE_FORM_FIELD requiere fieldId o fieldLabel.")
            return

        if not context.find_field(form, operation.field_id, operation.field_label):
            result.errors.append("DELETE_FORM_FIELD no encontro el campo indicado en el formulario.")

    def _validar_condicion_decision(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        node = self._require_existing_node(
            context,
            operation.node_id,
            operation.node_name,
            "UPDATE_DECISION_CONDITION",
            result,
        )
        if not node:
            return
        if str(node.get("type") or "").strip().lower() != "decision":
            result.errors.append("UPDATE_DECISION_CONDITION solo puede aplicarse a nodos decision.")
        if not self._text(operation.condition or operation.decision_condition):
            result.errors.append("UPDATE_DECISION_CONDITION requiere condition o decisionCondition.")

    def _validar_regla_negocio(
        self,
        context: "_WorkflowContext",
        operation: OperacionEdicionFlujo,
        result: ResultadoValidacionEdicion,
    ) -> None:
        if operation.type == "ADD_BUSINESS_RULE":
            if operation.node_id or operation.node_name:
                self._require_existing_node(context, operation.node_id, operation.node_name, "ADD_BUSINESS_RULE", result)
            if not operation.business_rule_name:
                result.warnings.append("ADD_BUSINESS_RULE no indica businessRuleName.")
            if not operation.expression:
                result.warnings.append("ADD_BUSINESS_RULE no indica expression.")
            return

        if operation.business_rule_id and context.find_business_rule(operation.business_rule_id, None):
            return
        if operation.business_rule_name and context.find_business_rule(None, operation.business_rule_name):
            return
        result.errors.append("DELETE_BUSINESS_RULE no encontro la regla indicada.")

    def _validar_riesgos_de_grafo(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        operations: list[OperacionEdicionFlujo],
        result: ResultadoValidacionEdicion,
    ) -> None:
        added_node_keys = set(added_nodes.keys())
        linked_new_nodes: set[str] = set()

        for operation in operations:
            if operation.type not in {"ADD_TRANSITION", "CREATE_LOOP"}:
                continue
            for node_name in [operation.from_node_name, operation.to_node_name]:
                node_key = self._normalize(node_name or "")
                if node_key in added_node_keys:
                    linked_new_nodes.add(node_key)

        for operation in operations:
            if operation.type != "ADD_NODE" or not operation.node_name:
                continue
            node_key = self._normalize(operation.node_name)
            has_reference = bool(operation.reference_node_id or operation.reference_node_name)
            if node_key not in linked_new_nodes and not has_reference:
                result.errors.append(
                    f"ADD_NODE crearia un nodo huerfano si no se agrega una transicion o referencia para {operation.node_name}."
                )

        for operation in operations:
            if operation.type != "DELETE_TRANSITION":
                continue
            transition = context.find_transition(
                transition_id=operation.transition_id,
                from_id=operation.from_node_id,
                from_name=operation.from_node_name,
                to_id=operation.to_node_id,
                to_name=operation.to_node_name,
            )
            if transition is not None:
                result.warnings.append(
                    "DELETE_TRANSITION puede afectar la conectividad basica; conviene previsualizar el grafo antes de aplicar."
                )

    def _require_existing_node(
        self,
        context: "_WorkflowContext",
        node_id: str | None,
        node_name: str | None,
        operation_type: str,
        result: ResultadoValidacionEdicion,
    ) -> dict[str, Any] | None:
        node = context.find_node(node_id, node_name)
        if node is not None:
            return node

        label = node_name or node_id or "<sin nodo>"
        result.errors.append(f"{operation_type} referencia un nodo inexistente: {label}.")
        return None

    def _resolve_node_reference(
        self,
        context: "_WorkflowContext",
        added_nodes: dict[str, str],
        node_id: str | None,
        node_name: str | None,
        role: str,
        operation_type: str,
        result: ResultadoValidacionEdicion,
    ) -> str | None:
        if node_id:
            if context.find_node(node_id, None):
                return node_id
            if node_id.startswith("new:"):
                return node_id
            result.errors.append(f"{operation_type} referencia {role} inexistente: {node_id}.")
            return None

        if not node_name:
            result.errors.append(f"{operation_type} requiere {role} mediante id o nombre.")
            return None

        node = context.find_node(None, node_name)
        if node is not None:
            return str(node.get("id"))

        node_key = self._normalize(node_name)
        if node_key in added_nodes:
            return added_nodes[node_key]

        result.errors.append(f"{operation_type} referencia {role} inexistente: {node_name}.")
        return None

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return " ".join(normalized.split())

    def _text(self, value: str | None) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip()
        return normalized or None

    def _deduplicate(self, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            key = value.strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)
        return unique

    validate = validar


class _WorkflowContext:
    NODE_TYPE_ALIASES = {
        "inicio": "start",
        "actividad": "task",
        "decision": "decision",
        "fork": "parallel_start",
        "join": "parallel_end",
        "fin": "end",
    }

    def __init__(self, workflow: dict[str, Any]) -> None:
        self.workflow = workflow
        self.nodes = self._as_list(workflow.get("nodes") or workflow.get("nodos"))
        self.transitions = [
            self._normalize_transition(transition, index)
            for index, transition in enumerate(
                self._as_list(workflow.get("transitions") or workflow.get("conexiones"))
            )
            if isinstance(transition, dict)
        ]
        self.forms = self._as_list(workflow.get("forms"))
        self.business_rules = self._as_list(workflow.get("businessRules"))
        self.nodes_by_id = {
            str(node.get("id")): node
            for node in self.nodes
            if isinstance(node, dict) and isinstance(node.get("id"), str)
        }

    def find_node(self, node_id: str | None, node_name: str | None) -> dict[str, Any] | None:
        if node_id and node_id in self.nodes_by_id:
            return self.nodes_by_id[node_id]
        found_id = self.find_node_id_by_name(node_name or "")
        if found_id:
            return self.nodes_by_id.get(found_id)
        return None

    def find_node_id_by_name(self, node_name: str) -> str | None:
        normalized_name = self._normalize(node_name)
        if not normalized_name:
            return None
        matches: list[str] = []
        fuzzy_matches: list[tuple[float, str]] = []
        for node in self.nodes:
            if not isinstance(node, dict):
                continue
            candidate_name = self._node_name(node)
            candidate_id = node.get("id")
            if not isinstance(candidate_name, str) or not isinstance(candidate_id, str):
                continue
            normalized_candidate = self._normalize(candidate_name)
            if normalized_candidate == normalized_name:
                matches.append(candidate_id)
                continue
            score = SequenceMatcher(None, normalized_candidate, normalized_name).ratio()
            if score >= 0.78:
                fuzzy_matches.append((score, candidate_id))
        if len(matches) == 1:
            return matches[0]
        if len(fuzzy_matches) == 1:
            return fuzzy_matches[0][1]
        if fuzzy_matches:
            fuzzy_matches.sort(reverse=True)
            best_score, best_id = fuzzy_matches[0]
            next_score = fuzzy_matches[1][0] if len(fuzzy_matches) > 1 else 0
            if best_score - next_score >= 0.08:
                return best_id
        return None

    def count_nodes_by_type(self, node_type: str) -> int:
        expected = node_type.strip().lower()
        return sum(
            1
            for node in self.nodes
            if isinstance(node, dict) and self._node_type(node) == expected
        )

    def node_type(self, node_id: str) -> str | None:
        node = self.nodes_by_id.get(node_id)
        if not node:
            return None
        return self._node_type(node)

    def transitions_connected_to(self, node_id: str) -> list[dict[str, Any]]:
        return [
            transition
            for transition in self.transitions
            if isinstance(transition, dict)
            and (transition.get("from") == node_id or transition.get("to") == node_id)
        ]

    def outgoing_count(self, node_id: str) -> int:
        return sum(
            1
            for transition in self.transitions
            if isinstance(transition, dict) and transition.get("from") == node_id
        )

    def has_transition(self, from_id: str, to_id: str) -> bool:
        return any(
            isinstance(transition, dict)
            and transition.get("from") == from_id
            and transition.get("to") == to_id
            for transition in self.transitions
        )

    def find_transition(
        self,
        *,
        transition_id: str | None,
        from_id: str | None,
        from_name: str | None,
        to_id: str | None,
        to_name: str | None,
    ) -> dict[str, Any] | None:
        if transition_id:
            for transition in self.transitions:
                if isinstance(transition, dict) and transition.get("id") == transition_id:
                    return transition

        resolved_from = from_id or self.find_node_id_by_name(from_name or "")
        resolved_to = to_id or self.find_node_id_by_name(to_name or "")
        if not resolved_from or not resolved_to:
            return None

        for transition in self.transitions:
            if not isinstance(transition, dict):
                continue
            if transition.get("from") == resolved_from and transition.get("to") == resolved_to:
                return transition
        return None

    def find_form(
        self,
        form_id: str | None,
        node_id: str | None,
        node_name: str | None,
    ) -> dict[str, Any] | None:
        resolved_node = node_id or self.find_node_id_by_name(node_name or "")
        for form in self.forms:
            if not isinstance(form, dict):
                continue
            if form_id and form.get("id") == form_id:
                return form
            if resolved_node and form.get("nodeId") == resolved_node:
                return form
        return None

    def find_field(
        self,
        form: dict[str, Any],
        field_id: str | None,
        field_label: str | None,
    ) -> dict[str, Any] | None:
        fields = self._as_list(form.get("fields"))
        normalized_label = self._normalize(field_label or "")
        for field in fields:
            if not isinstance(field, dict):
                continue
            if field_id and field.get("id") == field_id:
                return field
            if normalized_label and self._normalize(str(field.get("label") or "")) == normalized_label:
                return field
        return None

    def find_business_rule(self, rule_id: str | None, rule_name: str | None) -> dict[str, Any] | None:
        normalized_name = self._normalize(rule_name or "")
        for rule in self.business_rules:
            if not isinstance(rule, dict):
                continue
            if rule_id and rule.get("id") == rule_id:
                return rule
            if normalized_name and self._normalize(str(rule.get("name") or "")) == normalized_name:
                return rule
        return None

    def _as_list(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _node_name(self, node: dict[str, Any]) -> str | None:
        value = node.get("name") or node.get("nombre")
        return value if isinstance(value, str) else None

    def _node_type(self, node: dict[str, Any]) -> str | None:
        value = node.get("type") or node.get("tipo")
        if value is None:
            return None
        normalized = self._normalize(str(value))
        return self.NODE_TYPE_ALIASES.get(normalized, normalized)

    def _normalize_transition(self, transition: dict[str, Any], index: int) -> dict[str, Any]:
        normalized = dict(transition)
        normalized.setdefault("id", f"tr_{index}")
        normalized["from"] = transition.get("from") or transition.get("origen")
        normalized["to"] = transition.get("to") or transition.get("destino")
        return normalized

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return " ".join(normalized.split())


WorkflowEditValidator = ValidadorEdicionFlujo
