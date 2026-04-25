from typing import Any

from starlette.status import HTTP_400_BAD_REQUEST

from app.core.exceptions import ApiException


class ValidadorJsonFlujo:
    NODE_TYPES = {"start", "task", "decision", "parallel_start", "parallel_end", "end"}
    FIELD_TYPES = {"text", "textarea", "number", "date", "boolean", "select", "file", "email", "phone", "currency"}
    RESPONSIBLE_TYPES = {"department", "initiator"}

    def validate(self, workflow: dict[str, Any]) -> None:
        if not isinstance(workflow, dict) or not workflow:
            self._invalid("El workflow generado no puede estar vacio")

        self._require_object(workflow, "policy")
        departments = self._optional_array(workflow, "departments")
        roles = self._require_array(workflow, "roles", non_empty=True)
        nodes = self._require_array(workflow, "nodes", non_empty=True)
        transitions = self._require_array(workflow, "transitions", non_empty=True)
        forms = self._require_array(workflow, "forms", non_empty=False)
        business_rules = self._require_array(workflow, "businessRules", non_empty=False)
        self._require_object(workflow, "analysis")

        role_ids = self._validate_roles(roles)
        self._validate_departments(departments)
        node_types = self._validate_nodes(nodes, role_ids)
        self._validate_transitions(transitions, node_types)
        self._validate_forms(forms, node_types)
        self._validate_business_rules(business_rules, node_types)

    def _validate_departments(self, departments: list[Any]) -> None:
        department_ids: set[str] = set()

        for index, department in enumerate(departments):
            if not isinstance(department, dict):
                self._invalid(f"El departamento en posicion {index} debe ser un objeto")

            path = f"departments[{index}]"
            department_id = self._require_text(department, "id", path)
            department_name = self._require_text(department, "name", path)

            if department_id in department_ids:
                self._invalid(f"Id de departamento duplicado: {department_id}")
            department_ids.add(department_id)

            if len(department_name) < 2:
                self._invalid(f"El departamento {department_id} debe tener un nombre mas descriptivo")

    def _validate_roles(self, roles: list[Any]) -> set[str]:
        role_ids: set[str] = set()
        for index, role in enumerate(roles):
            if not isinstance(role, dict):
                self._invalid(f"El rol en posicion {index} debe ser un objeto")

            role_id = self._require_text(role, "id", f"roles[{index}]")
            self._require_text(role, "name", f"roles[{index}]")
            self._require_text(role, "description", f"roles[{index}]")

            if role_id in role_ids:
                self._invalid(f"Id de rol duplicado: {role_id}")
            role_ids.add(role_id)

        return role_ids

    def _validate_nodes(self, nodes: list[Any], role_ids: set[str]) -> dict[str, str]:
        node_types: dict[str, str] = {}
        has_start = False
        has_end = False

        for index, node in enumerate(nodes):
            if not isinstance(node, dict):
                self._invalid(f"El nodo en posicion {index} debe ser un objeto")

            path = f"nodes[{index}]"
            node_id = self._require_text(node, "id", path)
            node_type = self._require_text(node, "type", path)
            self._require_text(node, "name", path)
            self._require_text(node, "description", path)

            if node_type not in self.NODE_TYPES:
                self._invalid(f"Tipo de nodo invalido en {path}: {node_type}")

            if node_id in node_types:
                self._invalid(f"Id de nodo duplicado: {node_id}")
            node_types[node_id] = node_type

            has_start = has_start or node_type == "start"
            has_end = has_end or node_type == "end"

            if node_type == "task":
                responsible_role_id = self._require_text(node, "responsibleRoleId", path)
                if responsible_role_id not in role_ids:
                    self._invalid(f"El responsable del nodo {node_id} no existe en roles: {responsible_role_id}")

                responsible_type = self._optional_text(node, "responsibleType")
                if responsible_type is None:
                    self._invalid(f"El nodo task {node_id} debe incluir responsibleType")

                if responsible_type not in self.RESPONSIBLE_TYPES:
                    self._invalid(
                        f"El nodo task {node_id} tiene responsibleType invalido: {responsible_type}"
                    )

                if responsible_type == "department":
                    department_hint = self._optional_text(node, "departmentHint")
                    if not department_hint:
                        self._invalid(
                            f"El nodo task {node_id} con responsibleType=department debe incluir departmentHint"
                        )

        if not has_start:
            self._invalid("Debe existir al menos un nodo start")

        if not has_end:
            self._invalid("Debe existir al menos un nodo end")

        return node_types

    def _validate_transitions(self, transitions: list[Any], node_types: dict[str, str]) -> None:
        transition_ids: set[str] = set()
        outgoing_by_node: dict[str, int] = {}

        for index, transition in enumerate(transitions):
            if not isinstance(transition, dict):
                self._invalid(f"La transicion en posicion {index} debe ser un objeto")

            path = f"transitions[{index}]"
            transition_id = self._require_text(transition, "id", path)
            from_node = self._require_text(transition, "from", path)
            to_node = self._require_text(transition, "to", path)

            if transition_id in transition_ids:
                self._invalid(f"Id de transicion duplicado: {transition_id}")
            transition_ids.add(transition_id)

            if from_node not in node_types:
                self._invalid(f"La transicion {transition_id} referencia origen inexistente: {from_node}")

            if to_node not in node_types:
                self._invalid(f"La transicion {transition_id} referencia destino inexistente: {to_node}")

            outgoing_by_node[from_node] = outgoing_by_node.get(from_node, 0) + 1

        for node_id, node_type in node_types.items():
            outgoing = outgoing_by_node.get(node_id, 0)
            if node_type == "decision" and outgoing < 2:
                self._invalid(f"El nodo decision {node_id} debe tener multiples salidas")

            if node_type == "parallel_start" and outgoing < 2:
                self._invalid(f"El nodo parallel_start {node_id} debe tener multiples salidas")

    def _validate_forms(self, forms: list[Any], node_types: dict[str, str]) -> None:
        form_ids: set[str] = set()

        for index, form in enumerate(forms):
            if not isinstance(form, dict):
                self._invalid(f"El formulario en posicion {index} debe ser un objeto")

            path = f"forms[{index}]"
            form_id = self._require_text(form, "id", path)
            node_id = self._require_text(form, "nodeId", path)
            self._require_text(form, "name", path)

            if form_id in form_ids:
                self._invalid(f"Id de formulario duplicado: {form_id}")
            form_ids.add(form_id)

            if node_id not in node_types:
                self._invalid(f"El formulario {form_id} referencia nodo inexistente: {node_id}")

            if node_types[node_id] != "task":
                self._invalid(f"El formulario {form_id} debe pertenecer a un nodo task")

            fields = self._require_array(form, "fields", non_empty=False)
            for field_index, field in enumerate(fields):
                if not isinstance(field, dict):
                    self._invalid(f"El campo en {path}.fields[{field_index}] debe ser un objeto")

                field_path = f"{path}.fields[{field_index}]"
                self._require_text(field, "id", field_path)
                self._require_text(field, "label", field_path)
                field_type = self._require_text(field, "type", field_path)

                if field_type not in self.FIELD_TYPES:
                    self._invalid(f"Tipo de campo invalido en {field_path}: {field_type}")

                if "required" not in field or not isinstance(field["required"], bool):
                    self._invalid(f"El campo {field_path}.required debe ser boolean")

    def _validate_business_rules(self, business_rules: list[Any], node_types: dict[str, str]) -> None:
        rule_ids: set[str] = set()

        for index, rule in enumerate(business_rules):
            if not isinstance(rule, dict):
                self._invalid(f"La regla de negocio en posicion {index} debe ser un objeto")

            path = f"businessRules[{index}]"
            rule_id = self._require_text(rule, "id", path)
            self._require_text(rule, "name", path)
            self._require_text(rule, "description", path)
            self._require_text(rule, "expression", path)
            self._require_text(rule, "severity", path)

            if rule_id in rule_ids:
                self._invalid(f"Id de regla de negocio duplicado: {rule_id}")
            rule_ids.add(rule_id)

            applies_to_node_id = self._optional_text(rule, "appliesToNodeId")
            if applies_to_node_id and applies_to_node_id not in node_types:
                self._invalid(f"La regla {rule_id} referencia nodo inexistente: {applies_to_node_id}")

    def _require_object(self, parent: dict[str, Any], field: str) -> dict[str, Any]:
        value = parent.get(field)
        if not isinstance(value, dict) or not value:
            self._invalid(f"El campo {field} debe ser un objeto no vacio")
        return value

    def _require_array(self, parent: dict[str, Any], field: str, non_empty: bool) -> list[Any]:
        value = parent.get(field)
        if not isinstance(value, list):
            self._invalid(f"El campo {field} debe ser un arreglo")

        if non_empty and not value:
            self._invalid(f"El campo {field} no puede estar vacio")

        return value

    def _optional_array(self, parent: dict[str, Any], field: str) -> list[Any]:
        value = parent.get(field)
        if value is None:
            return []

        if not isinstance(value, list):
            self._invalid(f"El campo {field} debe ser un arreglo")

        return value

    def _require_text(self, parent: dict[str, Any], field: str, path: str) -> str:
        value = self._optional_text(parent, field)
        if value is None:
            self._invalid(f"El campo {path}.{field} es obligatorio")
        return value

    def _optional_text(self, parent: dict[str, Any], field: str) -> str | None:
        value = parent.get(field)
        if value is None:
            return None

        if not isinstance(value, str):
            self._invalid(f"El campo {field} debe ser texto")

        normalized = value.strip()
        return normalized or None

    def _invalid(self, message: str) -> None:
        raise ApiException(HTTP_400_BAD_REQUEST, f"Workflow IA invalido: {message}")

    validate = validate


WorkflowJsonValidator = ValidadorJsonFlujo
