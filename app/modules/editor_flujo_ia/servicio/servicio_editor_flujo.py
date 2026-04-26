import logging
import re
import unicodedata
from typing import Any

from pydantic import ValidationError

from app.modules.editor_flujo_ia.dominio.validador_edicion_flujo import ValidadorEdicionFlujo
from app.modules.editor_flujo_ia.modelos.respuesta_edicion_flujo import (
    IntencionEdicion,
    OperacionEdicionFlujo,
    RespuestaEdicionFlujo,
)
from app.modules.editor_flujo_ia.modelos.solicitud_edicion_flujo import SolicitudEdicionFlujo
from app.modules.editor_flujo_ia.prompts.prompts_editor_flujo import PromptsEditorFlujoIa
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class ServicioEditorFlujoIa:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsEditorFlujoIa,
        validator: ValidadorEdicionFlujo,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts
        self.validator = validator

    async def interpretar_edicion(self, request: SolicitudEdicionFlujo) -> RespuestaEdicionFlujo:
        warnings: list[str] = []
        payload: dict[str, Any] = {}

        try:
            raw_json = await self.prompt_runner.run_json_prompt(
                system_prompt=self.prompts.obtener_prompt_sistema(),
                user_prompt=self.prompts.obtener_prompt_usuario(request),
            )
            payload = self.json_parser.parse(raw_json)
        except Exception as exc:
            log.warning("No se pudo obtener respuesta valida de IA para edicion de flujo: %s", exc)
            warnings.append("No se pudo usar la IA en este intento; se aplico interpretacion local segura.")

        operations, operation_warnings = self._extract_operations(payload)
        warnings.extend(operation_warnings)

        if not operations:
            heuristic_operations, heuristic_warnings = self._infer_operations_locally(request)
            operations = heuristic_operations
            warnings.extend(heuristic_warnings)

        payload_warnings = self._extract_warnings(payload)
        warnings.extend(payload_warnings)

        validation = self.validator.validar(request.workflow, operations)
        if operations and validation.errors:
            heuristic_operations, heuristic_warnings = self._infer_operations_locally(request)
            if heuristic_operations:
                heuristic_validation = self.validator.validar(request.workflow, heuristic_operations)
                if heuristic_validation.is_valid:
                    operations = heuristic_operations
                    validation = heuristic_validation
                    warnings.append(
                        "La respuesta inicial de IA fue inconsistente; se recupero una interpretacion local segura."
                    )
                    warnings.extend(heuristic_warnings)
        warnings.extend(validation.warnings)
        warnings = self._deduplicate(warnings)
        errors = self._deduplicate(validation.errors)

        intent = self._build_intent(payload.get("intent"), operations, errors)
        summary = self._build_summary(payload.get("summary"), operations, warnings, errors)
        success = bool(operations) and not errors and intent == "UPDATE_WORKFLOW"

        return RespuestaEdicionFlujo(
            success=success,
            intent=intent,
            summary=summary,
            operations=operations if not errors else operations,
            warnings=warnings,
            errors=errors,
            requires_confirmation=True,
        )

    def _extract_operations(self, payload: dict[str, Any]) -> tuple[list[OperacionEdicionFlujo], list[str]]:
        raw_operations = payload.get("operations")
        if not isinstance(raw_operations, list):
            return [], []

        operations: list[OperacionEdicionFlujo] = []
        warnings: list[str] = []
        for index, item in enumerate(raw_operations):
            if not isinstance(item, dict):
                warnings.append(f"La operacion IA en posicion {index} no es un objeto y fue ignorada.")
                continue
            try:
                operations.append(OperacionEdicionFlujo.model_validate(item))
            except ValidationError:
                op_type = item.get("type") or "<sin tipo>"
                warnings.append(f"La operacion IA {op_type} en posicion {index} no coincide con el contrato y fue ignorada.")
        return operations, warnings

    def _infer_operations_locally(
        self,
        request: SolicitudEdicionFlujo,
    ) -> tuple[list[OperacionEdicionFlujo], list[str]]:
        prompt = request.prompt.strip()
        normalized = self._normalize(prompt)
        warnings: list[str] = []
        operations: list[OperacionEdicionFlujo] = []

        operation = self._detect_rename(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_loop(prompt)
        if operation:
            return [operation], warnings

        operations = self._detect_insert_activity_between(prompt)
        if operations:
            return operations, warnings

        operation = self._detect_delete_transition(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_add_transition(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_assign_responsible(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_form_update(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_add_decision(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_add_activity(prompt)
        if operation:
            return [operation], warnings

        operation = self._detect_add_node_with_inferred_position(prompt, request.workflow)
        if operation:
            return [operation], warnings

        operation = self._detect_delete_node(prompt)
        if operation:
            return [operation], warnings

        if self._looks_ambiguous(normalized):
            warnings.append(
                "La instruccion es ambigua para editar el flujo. Indica una accion concreta, nodo origen/destino o campo a modificar."
            )
            return operations, warnings

        warnings.append(
            "No se pudo convertir la instruccion en una operacion soportada con seguridad."
        )
        return operations, warnings

    def _detect_delete_node(self, prompt: str) -> OperacionEdicionFlujo | None:
        patterns = [
            r"\b(?:elimina|eliminar|borra|borrar|quita|quitar)\s+(?:la\s+|el\s+)?(?:actividad|nodo|tarea)?\s*(?P<node>.+)$",
        ]
        match = self._first_match(prompt, patterns)
        if not match:
            return None
        node_name = self._clean_node_name(match.group("node"))
        if not node_name:
            return None
        return OperacionEdicionFlujo(type="DELETE_NODE", node_name=node_name)

    def _detect_rename(self, prompt: str) -> OperacionEdicionFlujo | None:
        patterns = [
            r"\b(?:cambia|cambiar|renombra|renombrar)\s+(?:el\s+)?nombre\s+(?:de\s+)?(?:la\s+|el\s+)?(?:actividad|nodo|tarea)?\s*(?P<old>.+?)\s+a\s+(?P<new>.+)$",
            r"\b(?:cambia|cambiar|renombra|renombrar)\s+(?:la\s+|el\s+)?(?:actividad|nodo|tarea)\s+(?P<old>.+?)\s+a\s+(?P<new>.+)$",
        ]
        match = self._first_match(prompt, patterns)
        if not match:
            return None
        old_name = self._clean_node_name(match.group("old"))
        new_name = self._clean_node_name(match.group("new"))
        if not old_name or not new_name:
            return None
        return OperacionEdicionFlujo(type="RENAME_NODE", node_name=old_name, new_name=new_name)

    def _detect_loop(self, prompt: str) -> OperacionEdicionFlujo | None:
        normalized = self._normalize(prompt)
        if "loop" not in normalized and "vuelva" not in normalized and "volver" not in normalized:
            return None
        match = self._first_match(
            prompt,
            [
                r"\bdesde\s+(?P<from>.+?)\s+(?:hacia|a)\s+(?P<to>.+?)(?:\s+(?:cuando|si|con condicion)\s+(?P<condition>.+))?$",
                r"\b(?P<from>.+?)\s+(?:vuelva|volver)\s+(?:hacia|a)\s+(?P<to>.+?)(?:\s+(?:cuando|si|con condicion)\s+(?P<condition>.+))?$",
            ],
        )
        if not match:
            return None
        condition = self._clean_condition(match.groupdict().get("condition")) or "Requiere volver a la actividad anterior"
        return OperacionEdicionFlujo(
            type="CREATE_LOOP",
            from_node_name=self._clean_node_name(match.group("from")),
            to_node_name=self._clean_node_name(match.group("to")),
            condition=condition,
        )

    def _detect_add_transition(self, prompt: str) -> OperacionEdicionFlujo | None:
        patterns = [
            r"\bconecta\s+(?P<from>.+?)\s+con\s+(?P<to>.+?)(?:\s+(?:cuando|si|con condicion)\s+(?P<condition>.+))?$",
            r"\b(?:agrega|agregar|crea|crear)\s+(?:una\s+)?transici.n\s+(?:desde|entre)\s+(?P<from>.+?)\s+(?:hacia|a|y)\s+(?P<to>.+?)(?:\s+(?:cuando|si|con condicion)\s+(?P<condition>.+))?$",
        ]
        match = self._first_match(prompt, patterns)
        if not match:
            return None
        return OperacionEdicionFlujo(
            type="ADD_TRANSITION",
            from_node_name=self._clean_node_name(match.group("from")),
            to_node_name=self._clean_node_name(match.group("to")),
            condition=self._clean_condition(match.groupdict().get("condition")),
        )

    def _detect_delete_transition(self, prompt: str) -> OperacionEdicionFlujo | None:
        normalized = self._normalize(prompt)
        if "transicion" not in normalized:
            return None
        match = self._first_match(
            prompt,
            [
                r"\b(?:elimina|eliminar|borra|borrar|quita|quitar)\s+(?:la\s+)?transici.n\s+(?:entre|desde)\s+(?P<from>.+?)\s+(?:y|hacia|a)\s+(?P<to>.+)$",
            ],
        )
        if not match:
            return None
        return OperacionEdicionFlujo(
            type="DELETE_TRANSITION",
            from_node_name=self._clean_node_name(match.group("from")),
            to_node_name=self._clean_node_name(match.group("to")),
        )

    def _detect_assign_responsible(self, prompt: str) -> OperacionEdicionFlujo | None:
        match = self._first_match(
            prompt,
            [
                r"\basigna\s+como\s+responsable\s+de\s+(?P<node>.+?)\s+a\s+(?P<responsible>.+)$",
                r"\bhaz\s+que\s+(?P<responsible>.+?)\s+sea\s+responsable\s+de\s+(?:la\s+|el\s+)?(?:actividad|nodo|tarea)?\s*(?P<node>.+)$",
            ],
        )
        if not match:
            return None
        responsible = self._clean_node_name(match.group("responsible"))
        responsible_normalized = self._normalize(responsible)
        if any(token in responsible_normalized for token in ["quien inicio", "iniciador", "solicitante", "quien inicio el tramite"]):
            return OperacionEdicionFlujo(
                type="ASSIGN_RESPONSIBLE",
                node_name=self._clean_node_name(match.group("node")),
                responsible_type="initiator",
                responsible_role_name="Iniciador",
            )
        return OperacionEdicionFlujo(
            type="ASSIGN_RESPONSIBLE",
            node_name=self._clean_node_name(match.group("node")),
            responsible_type="department",
            responsible_role_name=responsible,
            department_hint=responsible,
        )

    def _detect_form_update(self, prompt: str) -> OperacionEdicionFlujo | None:
        normalized = self._normalize(prompt)
        if "formulario" not in normalized:
            return None
        match = self._first_match(
            prompt,
            [
                r"\b(?:agrega|agregar|crea|crear)\s+(?:un\s+)?formulario\s+a\s+(?:la\s+|el\s+)?(?:actividad|nodo|tarea)?\s*(?P<node>.+)$",
            ],
        )
        if not match:
            return None
        node_name = self._clean_node_name(match.group("node"))
        return OperacionEdicionFlujo(
            type="UPDATE_FORM",
            node_name=node_name,
            form_name=f"Formulario {node_name}",
        )

    def _detect_add_decision(self, prompt: str) -> OperacionEdicionFlujo | None:
        normalized = self._normalize(prompt)
        if "decision" not in normalized:
            return None
        match = self._first_match(
            prompt,
            [
                r"\b(?:agrega|agregar|crea|crear)\s+(?:una\s+)?decisi.n\s+(?P<position>despues|despu.s|antes)\s+de\s+(?P<reference>.+)$",
            ],
        )
        if not match:
            return None
        position = "after" if self._normalize(match.group("position")) == "despues" else "before"
        return OperacionEdicionFlujo(
            type="ADD_NODE",
            node_name="Decidir siguiente paso",
            node_type="decision",
            reference_node_name=self._clean_node_name(match.group("reference")),
            position=position,
            description="Decision agregada por instruccion de edicion IA.",
        )

    def _detect_add_activity(self, prompt: str) -> OperacionEdicionFlujo | None:
        match = self._first_match(
            prompt,
            [
                r"\b(?:agrega|agregar|crea|crear)\s+(?:una\s+)?actividad\s+(?P<position>despues|despu.s|antes)\s+de\s+(?P<reference>.+?)\s+llamada\s+(?P<name>.+)$",
                r"\b(?:agrega|agregar|crea|crear)\s+(?:una\s+)?actividad\s+llamada\s+(?P<name>.+?)\s+(?P<position>despues|despu.s|antes)\s+de\s+(?P<reference>.+)$",
                r"\b(?:agrega|agregar|crea|crear|anade|anadir|anadime)\s+(?:una\s+)?(?:actividad|tarea)\s+(?:para\s+)?(?P<purpose>.+?)\s+(?P<position>despues|despu.s|antes)\s+de\s+(?P<reference>.+)$",
            ],
        )
        if not match:
            return None
        position = "after" if self._normalize(match.group("position")) == "despues" else "before"
        group_values = match.groupdict()
        node_name = self._clean_node_name(group_values.get("name"))
        if not node_name:
            node_name = self._build_activity_name_from_purpose(
                group_values.get("purpose"),
                group_values.get("reference"),
                prompt,
            )
        return OperacionEdicionFlujo(
            type="ADD_NODE",
            node_name=node_name,
            node_type="task",
            reference_node_name=self._clean_node_name(match.group("reference")),
            position=position,
            description="Actividad agregada por instruccion de edicion IA.",
        )

    def _detect_insert_activity_between(self, prompt: str) -> list[OperacionEdicionFlujo]:
        match = self._first_match(
            prompt,
            [
                r"\b(?:agrega|agregar|crea|crear|anade|anadir|anadime)\s+(?:un\s+)?(?:nodo\s+de\s+)?(?:actividad|tarea)\s+(?:llamad[ao]\s+)?(?P<name>.+?)\s+entre\s+(?P<from>.+?)\s+(?:y|e)\s+(?P<to>.+)$",
                r"\b(?:agrega|agregar|crea|crear|anade|anadir|anadime)\s+entre\s+(?P<from>.+?)\s+(?:y|e)\s+(?P<to>.+?)\s+(?:un\s+)?(?:nodo\s+de\s+)?(?:actividad|tarea)\s+(?:llamad[ao]\s+)?(?P<name>.+)$",
            ],
        )
        if not match:
            return []

        node_name = self._clean_node_name(match.group("name"))
        from_node_name = self._clean_quoted_node_name(match.group("from"))
        to_node_name = self._clean_quoted_node_name(match.group("to"))
        if not node_name or not from_node_name or not to_node_name:
            return []

        return [
            OperacionEdicionFlujo(
                type="ADD_NODE",
                node_name=node_name,
                node_type="task",
                reference_node_name=from_node_name,
                position="after",
                description="Actividad insertada entre dos nodos existentes.",
            ),
            OperacionEdicionFlujo(
                type="DELETE_TRANSITION",
                from_node_name=from_node_name,
                to_node_name=to_node_name,
            ),
            OperacionEdicionFlujo(
                type="ADD_TRANSITION",
                from_node_name=from_node_name,
                to_node_name=node_name,
            ),
            OperacionEdicionFlujo(
                type="ADD_TRANSITION",
                from_node_name=node_name,
                to_node_name=to_node_name,
            ),
        ]

    def _detect_add_node_with_inferred_position(
        self,
        prompt: str,
        workflow: dict[str, Any],
    ) -> OperacionEdicionFlujo | None:
        normalized = self._normalize(prompt)
        if not any(token in normalized for token in ["agrega", "agregar", "crea", "crear", "anade", "anadir", "anadime"]):
            return None
        if not any(token in normalized for token in ["nodo", "actividad", "tarea"]):
            return None

        match = self._first_match(
            prompt,
            [
                r"\b(?:agrega|agregar|crea|crear|anade|anadir|anadime)\s+(?:el\s+|un\s+|una\s+)?(?:nodo|actividad|tarea)\s+(?:llamad[ao]\s+)?(?P<name>.+)$",
            ],
        )
        if not match:
            return None

        node_name = self._clean_node_name(match.group("name"))
        if not node_name:
            return None

        reference_name = self._find_node_name_by_tokens(workflow, ["solicitar", "datos"])
        if not reference_name:
            reference_name = self._first_activity_node_name(workflow)
        if not reference_name:
            return None

        return OperacionEdicionFlujo(
            type="ADD_NODE",
            node_name=node_name[:1].upper() + node_name[1:],
            node_type="task",
            reference_node_name=reference_name,
            position="after",
            description="Actividad agregada por instruccion de edicion IA.",
        )

    def _build_intent(
        self,
        raw_intent: Any,
        operations: list[OperacionEdicionFlujo],
        errors: list[str],
    ) -> IntencionEdicion:
        if errors:
            return "NEEDS_CLARIFICATION"
        if operations:
            return "UPDATE_WORKFLOW"
        if raw_intent in {"NEEDS_CLARIFICATION", "UNSUPPORTED_REQUEST"}:
            return raw_intent
        return "NEEDS_CLARIFICATION"

    def _build_summary(
        self,
        raw_summary: Any,
        operations: list[OperacionEdicionFlujo],
        warnings: list[str],
        errors: list[str],
    ) -> str:
        if isinstance(raw_summary, str) and raw_summary.strip():
            return raw_summary.strip()[:500]
        if errors:
            return "La edicion propuesta necesita correccion antes de previsualizarse."
        if not operations:
            return "No se detectaron cambios seguros para el flujo."
        if len(operations) == 1:
            operation = operations[0]
            return self._summarize_operation(operation)
        if warnings:
            return f"Se detectaron {len(operations)} operacion(es), con advertencias para revisar antes de aplicar."
        return f"Se detectaron {len(operations)} operacion(es) de edicion para previsualizar."

    def _summarize_operation(self, operation: OperacionEdicionFlujo) -> str:
        if operation.type in {"ADD_TRANSITION", "CREATE_LOOP"}:
            return (
                f"Se propone conectar {operation.from_node_name or operation.from_node_id} "
                f"con {operation.to_node_name or operation.to_node_id}."
            )
        if operation.type == "DELETE_NODE":
            return f"Se propone eliminar el nodo {operation.node_name or operation.node_id}."
        if operation.type == "RENAME_NODE":
            return f"Se propone renombrar {operation.node_name or operation.node_id} a {operation.new_name}."
        if operation.type == "ASSIGN_RESPONSIBLE":
            return f"Se propone reasignar el responsable de {operation.node_name or operation.node_id}."
        return f"Se propone aplicar la operacion {operation.type}."

    def _extract_warnings(self, payload: dict[str, Any]) -> list[str]:
        raw_warnings = payload.get("warnings")
        if not isinstance(raw_warnings, list):
            return []
        return [warning.strip() for warning in raw_warnings if isinstance(warning, str) and warning.strip()]

    def _looks_ambiguous(self, normalized_prompt: str) -> bool:
        ambiguous = {
            "mejora el flujo",
            "mejora esto",
            "arregla el flujo",
            "optimizalo",
            "hazlo mejor",
            "cambia el flujo",
        }
        return normalized_prompt in ambiguous or len(normalized_prompt.split()) <= 2

    def _first_match(self, prompt: str, patterns: list[str]) -> re.Match[str] | None:
        candidates = [prompt.strip()]
        normalized_prompt = self._normalize(prompt)
        if normalized_prompt and normalized_prompt != candidates[0]:
            candidates.append(normalized_prompt)
        for pattern in patterns:
            for candidate in candidates:
                match = re.search(pattern, candidate, flags=re.IGNORECASE)
                if match:
                    return match
        return None

    def _clean_node_name(self, value: str | None) -> str:
        if not value:
            return ""
        cleaned = value.strip().strip(" .,:;\"'")
        stop_words = [" con condicion ", " cuando ", " si "]
        normalized = self._normalize(cleaned)
        for stop_word in stop_words:
            stop_index = normalized.find(stop_word.strip())
            if stop_index > 0:
                return " ".join(cleaned.split()[: len(normalized[:stop_index].split())]).strip()
        return cleaned

    def _clean_quoted_node_name(self, value: str | None) -> str:
        cleaned = self._clean_node_name(value)
        if not cleaned:
            return ""
        if len(cleaned) >= 2 and cleaned[0] == cleaned[-1] and cleaned[0] in {"'", '"'}:
            return cleaned[1:-1].strip()
        return cleaned

    def _build_activity_name_from_purpose(
        self,
        purpose: str | None,
        reference: str | None,
        prompt: str,
    ) -> str:
        cleaned = self._clean_node_name(purpose)
        if not cleaned:
            return "Nueva actividad"

        normalized_context = self._normalize(" ".join([prompt, reference or ""]))
        normalized_purpose = self._normalize(cleaned)
        if "foto" in normalized_purpose and "pacient" in normalized_context:
            return "Pedir foto del paciente"

        cleaned = re.sub(
            r"\b(?:al|a\s+la|a\s+el|del|de\s+la|de\s+el)\s+(?:usuario|solicitante|paciente)\b",
            "",
            cleaned,
            flags=re.IGNORECASE,
        )
        cleaned = " ".join(cleaned.split())
        if not cleaned:
            return "Nueva actividad"
        return cleaned[:1].upper() + cleaned[1:]

    def _clean_condition(self, value: str | None) -> str | None:
        if not value:
            return None
        cleaned = value.strip().strip(" .,:;\"'")
        return cleaned or None

    def _workflow_nodes(self, workflow: dict[str, Any]) -> list[Any]:
        nodes = workflow.get("nodes") or workflow.get("nodos")
        return nodes if isinstance(nodes, list) else []

    def _node_name(self, node: Any) -> str:
        if not isinstance(node, dict):
            return ""
        value = node.get("name") or node.get("nombre")
        return value if isinstance(value, str) else ""

    def _node_type(self, node: Any) -> str:
        if not isinstance(node, dict):
            return ""
        value = node.get("type") or node.get("tipo")
        return self._normalize(str(value or ""))

    def _find_node_name_by_tokens(self, workflow: dict[str, Any], tokens: list[str]) -> str:
        for node in self._workflow_nodes(workflow):
            node_name = self._node_name(node)
            normalized_name = self._normalize(node_name)
            if node_name and all(token in normalized_name for token in tokens):
                return node_name
        return ""

    def _first_activity_node_name(self, workflow: dict[str, Any]) -> str:
        for node in self._workflow_nodes(workflow):
            node_type = self._node_type(node)
            if node_type in {"task", "actividad"}:
                return self._node_name(node)
        return ""

    def _normalize(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        return " ".join(normalized.split())

    def _deduplicate(self, values: list[str]) -> list[str]:
        unique: list[str] = []
        seen: set[str] = set()
        for value in values:
            key = value.strip()
            if key and key not in seen:
                seen.add(key)
                unique.append(key)
        return unique

    edit_workflow = interpretar_edicion


WorkflowEditorAiService = ServicioEditorFlujoIa
