import logging
import unicodedata
from typing import Any

from app.modules.asistente_formularios.prompts.prompts_llenado_formulario import PromptsLlenadoFormulario
from app.modules.asistente_formularios.modelos.solicitud_llenado_formulario import FormFieldSchema, FormFillRequest
from app.modules.asistente_formularios.modelos.respuesta_llenado_formulario import FormFieldChange, FormFillResponse
from app.modules.asistente_formularios.validadores.validador_campos_formulario import ValidadorCamposFormulario
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class ServicioAsistenteFormularios:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsLlenadoFormulario,
        field_validator: ValidadorCamposFormulario,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts
        self.field_validator = field_validator

    async def llenar_formulario(self, request: FormFillRequest) -> FormFillResponse:
        base_values = self.field_validator.build_base_values(request.form_schema, request.current_values)
        warnings: list[str] = []
        ai_payload: dict[str, Any] = {}

        try:
            raw_json = await self.prompt_runner.run_json_prompt(
                system_prompt=self.prompts.obtener_prompt_sistema(),
                user_prompt=self.prompts.obtener_prompt_usuario(request),
            )
            ai_payload = self.json_parser.parse(raw_json)
        except Exception as exc:
            log.warning("No se pudo obtener respuesta valida de IA para llenado de formulario: %s", exc)
            warnings.append("No se pudo usar la IA en este intento; se aplicaron reglas locales seguras.")

        heuristic_values, heuristic_reasons, heuristic_warnings = self._apply_heuristics(request, base_values)
        warnings.extend(heuristic_warnings)

        ai_candidate_values = ai_payload.get("updatedValues")
        if not isinstance(ai_candidate_values, dict):
            ai_candidate_values = {}

        merged_candidate_values = dict(ai_candidate_values)
        for field_id, value in heuristic_values.items():
            if field_id not in merged_candidate_values:
                merged_candidate_values[field_id] = value

        sanitized = self.field_validator.sanitize_updated_values(
            fields=request.form_schema,
            base_values=base_values,
            candidate_values=merged_candidate_values,
        )
        warnings.extend(sanitized.warnings)

        changes = self._build_changes(
            fields=request.form_schema,
            old_values=base_values,
            new_values=sanitized.updated_values,
            ai_changes=ai_payload.get("changes"),
            heuristic_reasons=heuristic_reasons,
        )
        changed_values = {
            change.field_id: change.new_value
            for change in changes
        }

        warnings.extend(self._required_field_warnings(request.form_schema, sanitized.updated_values, request.user_prompt))
        warnings.extend(self._generic_prompt_guidance(request.form_schema, request.user_prompt, changes))
        warnings.extend(self._extract_warnings(ai_payload))
        warnings = self._deduplicate(warnings)

        confidence = self._build_confidence(ai_payload.get("confidence"), changes, warnings)
        message = self._build_message(
            ai_payload.get("message"),
            request.form_schema,
            request.user_prompt,
            changes,
            warnings,
        )

        return FormFillResponse(
            success=True,
            updated_values=changed_values,
            changes=changes,
            warnings=warnings,
            confidence=confidence,
            message=message,
        )

    def _build_changes(
        self,
        *,
        fields: list[FormFieldSchema],
        old_values: dict[str, Any],
        new_values: dict[str, Any],
        ai_changes: Any,
        heuristic_reasons: dict[str, str],
    ) -> list[FormFieldChange]:
        ai_reason_map = self._extract_ai_reason_map(ai_changes)
        changes: list[FormFieldChange] = []

        for field in fields:
            old_value = old_values.get(field.id)
            new_value = new_values.get(field.id)
            if old_value == new_value:
                continue

            reason = ai_reason_map.get(field.id) or heuristic_reasons.get(field.id) or "Se aplico la instruccion del usuario."
            changes.append(
                FormFieldChange(
                    field_id=field.id,
                    old_value=old_value,
                    new_value=new_value,
                    reason=reason,
                )
            )

        return changes

    def _extract_ai_reason_map(self, ai_changes: Any) -> dict[str, str]:
        if not isinstance(ai_changes, list):
            return {}

        reasons: dict[str, str] = {}
        for item in ai_changes:
            if not isinstance(item, dict):
                continue
            field_id = item.get("fieldId")
            reason = item.get("reason")
            if isinstance(field_id, str) and field_id.strip() and isinstance(reason, str) and reason.strip():
                reasons[field_id.strip()] = reason.strip()
        return reasons

    def _extract_warnings(self, ai_payload: dict[str, Any]) -> list[str]:
        raw_warnings = ai_payload.get("warnings")
        if not isinstance(raw_warnings, list):
            return []
        return [warning.strip() for warning in raw_warnings if isinstance(warning, str) and warning.strip()]

    def _build_confidence(self, ai_confidence: Any, changes: list[FormFieldChange], warnings: list[str]) -> float:
        try:
            confidence = float(ai_confidence)
        except (TypeError, ValueError):
            confidence = 0.88 if changes else 0.45

        confidence = max(0.0, min(1.0, confidence))
        confidence -= min(0.3, len(warnings) * 0.08)
        if not changes:
            confidence = min(confidence, 0.55)
        return round(max(0.0, confidence), 2)

    def _build_message(
        self,
        ai_message: Any,
        fields: list[FormFieldSchema],
        user_prompt: str,
        changes: list[FormFieldChange],
        warnings: list[str],
    ) -> str:
        if isinstance(ai_message, str) and ai_message.strip():
            cleaned = ai_message.strip()[:200]
            if changes or not warnings:
                return cleaned
        if changes:
            return "Formulario actualizado correctamente con IA."
        if self._is_generic_fill_prompt(user_prompt):
            candidate_fields = ", ".join(self._suggestible_fields(fields[:3]))
            if candidate_fields:
                return (
                    "La instruccion es demasiado general para completar campos con seguridad. "
                    f"Indica que valor deseas colocar en: {candidate_fields}."
                )[:200]
            return "La instruccion es demasiado general para completar el formulario con seguridad."
        if warnings:
            return "No se realizaron cambios seguros en el formulario."
        return "Formulario procesado correctamente."

    def _required_field_warnings(
        self,
        fields: list[FormFieldSchema],
        updated_values: dict[str, Any],
        user_prompt: str,
    ) -> list[str]:
        warnings: list[str] = []
        prompt_normalized = self._normalize_text(user_prompt)
        prompt_has_action = any(token in prompt_normalized for token in ["aprueba", "rechaza", "observa", "completa", "llena"])
        if not prompt_has_action:
            return warnings

        for field in fields:
            if not field.required:
                continue
            if updated_values.get(field.id) in {None, ""}:
                warnings.append(f"No fue posible inferir con seguridad el campo requerido '{field.id}'.")
        return warnings

    def _generic_prompt_guidance(
        self,
        fields: list[FormFieldSchema],
        user_prompt: str,
        changes: list[FormFieldChange],
    ) -> list[str]:
        if changes or not self._is_generic_fill_prompt(user_prompt):
            return []

        candidate_fields = self._suggestible_fields(fields[:3])
        if candidate_fields:
            return [
                "El prompt expresa intencion de completar el formulario, pero no especifica valores concretos. "
                f"Prueba indicando un valor o decision para: {', '.join(candidate_fields)}."
            ]

        return [
            "El prompt expresa intencion de completar el formulario, pero no especifica valores concretos."
        ]

    def _apply_heuristics(
        self,
        request: FormFillRequest,
        base_values: dict[str, Any],
    ) -> tuple[dict[str, Any], dict[str, str], list[str]]:
        prompt = self._normalize_text(request.user_prompt)
        values: dict[str, Any] = {}
        reasons: dict[str, str] = {}
        warnings: list[str] = []

        decision_intent = self._detect_decision_intent(prompt)
        document_intent = self._detect_document_intent(prompt)
        wants_comment = any(token in prompt for token in ["observacion", "explicacion", "motivo", "comentario", "justificacion"])

        for field in request.form_schema:
            field_key = self._normalize_text(f"{field.id} {field.label}")

            if field.type == "select" and decision_intent and self._is_decision_field(field_key, field.options):
                option = self._pick_select_option(decision_intent, field.options)
                if option is not None:
                    values[field.id] = option
                    reasons[field.id] = self._build_decision_reason(decision_intent)
                    continue

            if field.type == "boolean":
                bool_value = self._infer_boolean_value(field_key, prompt, decision_intent, document_intent)
                if bool_value is not None:
                    values[field.id] = bool_value
                    reasons[field.id] = "Se ajusto el valor booleano segun la instruccion del usuario."
                    continue

            if field.type in {"text", "textarea"} and wants_comment and self._is_comment_field(field_key):
                if not base_values.get(field.id):
                    values[field.id] = self._build_observation_text(prompt, decision_intent, document_intent)
                    reasons[field.id] = "Se genero un texto breve y formal a partir del prompt."

        if "archivo" in prompt or "adjunta" in prompt or "adjuntar" in prompt:
            warnings.append("Los archivos no se completan automaticamente; solo se conserva metadata existente.")

        return values, reasons, warnings

    def _is_generic_fill_prompt(self, prompt: str) -> bool:
        normalized = self._normalize_text(prompt)
        fill_tokens = [
            "rellena",
            "rellename",
            "rellenes",
            "rellenar",
            "llena",
            "llenes",
            "llenar",
            "completa",
            "completar",
            "completame",
        ]
        vague_tokens = [
            "como sea",
            "como puedas",
            "automaticamente",
            "hazlo",
            "hazlo tu",
            "por favor",
        ]

        has_fill_intent = any(token in normalized for token in fill_tokens)
        lacks_specific_intent = (
            self._detect_decision_intent(normalized) is None
            and self._detect_document_intent(normalized) is None
            and not any(
                token in normalized
                for token in [
                    "observacion",
                    "explicacion",
                    "motivo",
                    "comentario",
                    "justificacion",
                    "fecha",
                    "precio",
                    "monto",
                    "importe",
                    "numero",
                    "valor",
                ]
            )
        )
        is_vague = any(token in normalized for token in vague_tokens)
        return has_fill_intent and (lacks_specific_intent or is_vague)

    def _suggestible_fields(self, fields: list[FormFieldSchema]) -> list[str]:
        labels: list[str] = []
        for field in fields:
            label = field.label.strip() if field.label.strip() else field.id
            labels.append(label)
        return labels

    def _detect_decision_intent(self, prompt: str) -> str | None:
        if any(token in prompt for token in ["rechaza", "rechazar", "rechazado", "no viable", "inviable", "deniega"]):
            return "rechazado"
        if any(token in prompt for token in ["observa", "observado", "observacion"]):
            return "observado"
        if any(token in prompt for token in ["aprueba", "aprobar", "aprobado", "viable"]):
            return "aprobado"
        return None

    def _detect_document_intent(self, prompt: str) -> bool | None:
        positive_tokens = ["faltan documentos", "falta documento", "documentos adicionales", "no presento", "faltan requisitos"]
        negative_tokens = ["no requiere documentos", "sin documentos adicionales"]
        if any(token in prompt for token in positive_tokens):
            return True
        if any(token in prompt for token in negative_tokens):
            return False
        return None

    def _infer_boolean_value(
        self,
        field_key: str,
        prompt: str,
        decision_intent: str | None,
        document_intent: bool | None,
    ) -> bool | None:
        is_document_field = any(token in field_key for token in ["document", "requisito", "adjunto", "archivo"])
        if is_document_field and document_intent is not None:
            return document_intent

        if any(token in field_key for token in ["aprob", "viable", "acept", "decision", "resultado"]):
            if decision_intent == "aprobado":
                return True
            if decision_intent in {"rechazado", "observado"}:
                return False

        if "no viable" in prompt and "viable" in field_key:
            return False

        return None

    def _pick_select_option(self, decision_intent: str, options: list[str]) -> str | None:
        canonical_map = {
            "aprobado": ["aprobado", "aprobada", "viable", "aceptado", "si"],
            "rechazado": ["rechazado", "rechazada", "no viable", "inviable", "denegado", "no"],
            "observado": ["observado", "observada", "observacion"],
        }
        for option in options:
            normalized_option = self._normalize_text(option)
            if normalized_option in {self._normalize_text(item) for item in canonical_map[decision_intent]}:
                return option

        for option in options:
            if self._normalize_text(decision_intent) in self._normalize_text(option):
                return option

        return None

    def _is_decision_field(self, field_key: str, options: list[str]) -> bool:
        option_keys = " ".join(self._normalize_text(option) for option in options)
        return any(token in field_key for token in ["decision", "estado", "resultado", "dictamen", "revision", "viable"]) or any(
            token in option_keys for token in ["aprobado", "rechazado", "observado", "viable", "inviable"]
        )

    def _is_comment_field(self, field_key: str) -> bool:
        return any(token in field_key for token in ["observ", "coment", "motivo", "justif", "detalle", "descripcion", "explic"])

    def _build_observation_text(
        self,
        prompt: str,
        decision_intent: str | None,
        document_intent: bool | None,
    ) -> str:
        if document_intent is True and decision_intent == "rechazado":
            return "La solicitud fue rechazada debido a la falta de documentos requeridos para continuar con el tramite."
        if document_intent is True:
            return "Se deja constancia de que faltan documentos requeridos para continuar con el tramite."
        if decision_intent == "aprobado":
            return "La revision fue aprobada y no se identificaron observaciones relevantes."
        if decision_intent == "observado":
            return "La solicitud queda en observacion para su seguimiento y ajuste correspondiente."
        if decision_intent == "rechazado":
            return "La solicitud fue rechazada conforme a la instruccion indicada en el formulario."
        if "formal" in prompt or "clara" in prompt:
            return "Se registra una respuesta formal y clara para la gestion del tramite."
        return "Se actualizo el formulario conforme a la instruccion del usuario."

    def _build_decision_reason(self, decision_intent: str) -> str:
        if decision_intent == "aprobado":
            return "El usuario solicito aprobar la decision."
        if decision_intent == "observado":
            return "El usuario solicito dejar la decision en observacion."
        return "El usuario solicito rechazar la decision."

    def _normalize_text(self, value: str) -> str:
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

    fill_form = llenar_formulario


FormAiService = ServicioAsistenteFormularios
