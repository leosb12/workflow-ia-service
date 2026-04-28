import logging
import time
from typing import Any

from pydantic import ValidationError

from app.modules.guia_usuario.comun.solicitud_guia import EmployeeGuideRequest
from app.modules.guia_usuario.comun.respuesta_guia import (
    EmployeeFormHelp,
    EmployeeGuideIntent,
    EmployeeGuideResponse,
    EmployeeMissingField,
    EmployeePrioritySuggestion,
    GuideSeverity,
    SuggestedAction,
)
from app.modules.guia_usuario.funcionario.respaldo_guia_funcionario import (
    RespaldoGuiaFuncionario,
)
from app.modules.guia_usuario.funcionario.clasificador_intencion_funcionario import (
    ClasificadorIntencionFuncionario,
)
from app.modules.guia_usuario.funcionario.prompts_guia_funcionario import PromptsGuiaFuncionario
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class ServicioGuiaFuncionario:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsGuiaFuncionario,
        classifier: ClasificadorIntencionFuncionario,
        fallback_service: RespaldoGuiaFuncionario,
        llm_model: str,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts
        self.classifier = classifier
        self.fallback_service = fallback_service
        self.llm_model = llm_model

    async def guiar_funcionario(self, request: EmployeeGuideRequest) -> EmployeeGuideResponse:
        request_started_at = time.perf_counter()
        log.info("[TIMING][Guide] Inicio guide_employee")

        intent_started_at = time.perf_counter()
        intent = self.classifier.detect(request.question, request.screen)
        log.info(
            "[TIMING][Guide] detect employee intent en %.3fs intent=%s",
            time.perf_counter() - intent_started_at,
            intent.value,
        )

        fallback_started_at = time.perf_counter()
        fallback_response = self.fallback_service.build_response(request, intent)
        log.info(
            "[TIMING][Guide] build employee fallback en %.3fs",
            time.perf_counter() - fallback_started_at,
        )

        if request.screen.name == "PERFIL_USUARIO":
            log.info(
                "[TIMING][Guide] employee profile screen usa fallback directo en %.3fs",
                time.perf_counter() - request_started_at,
            )
            return fallback_response

        try:
            llm_started_at = time.perf_counter()
            raw_json = await self.prompt_runner.run_json_prompt(
                system_prompt=self.prompts.obtener_prompt_sistema(),
                user_prompt=self.prompts.obtener_prompt_usuario(
                    request=request,
                    intent=intent,
                    fallback_response=fallback_response,
                ),
                model_override=self.llm_model,
            )
            log.info(
                "[TIMING][Guide] employee run_json_prompt en %.3fs model=%s",
                time.perf_counter() - llm_started_at,
                self.llm_model,
            )

            parse_started_at = time.perf_counter()
            payload = self.json_parser.parse(raw_json)
            log.info(
                "[TIMING][Guide] employee json_parser.parse en %.3fs",
                time.perf_counter() - parse_started_at,
            )

            sanitize_started_at = time.perf_counter()
            response = self._sanitize_response(payload, fallback_response, intent)
            log.info(
                "[TIMING][Guide] employee sanitize_response en %.3fs",
                time.perf_counter() - sanitize_started_at,
            )
            log.info(
                "[TIMING][Guide] guide_employee total en %.3fs source=%s",
                time.perf_counter() - request_started_at,
                response.source,
            )
            return response
        except Exception as exc:
            log.warning("No se pudo completar employee guide con IA. Se usa fallback: %s", exc)
            log.info(
                "[TIMING][Guide] guide_employee total con fallback en %.3fs",
                time.perf_counter() - request_started_at,
            )
            return fallback_response

    def _sanitize_response(
        self,
        payload: dict[str, Any],
        fallback_response: EmployeeGuideResponse,
        intent: EmployeeGuideIntent,
    ) -> EmployeeGuideResponse:
        try:
            answer = self._clean_text(payload.get("answer")) or fallback_response.answer
            steps = self._clean_list(payload.get("steps")) or fallback_response.steps
            severity = self._normalize_severity(payload.get("severity")) or fallback_response.severity
            form_help = self._sanitize_form_help(payload.get("formHelp")) or fallback_response.form_help
            missing_fields = self._sanitize_missing_fields(payload.get("missingFields")) or fallback_response.missing_fields
            priority_suggestion = self._sanitize_priority_suggestion(payload.get("prioritySuggestion"))
            if priority_suggestion is None:
                priority_suggestion = fallback_response.priority_suggestion
            next_step_explanation = (
                self._clean_text(payload.get("nextStepExplanation"))
                or fallback_response.next_step_explanation
            )
            suggested_actions = self._merge_actions(
                self._sanitize_actions(payload.get("suggestedActions")),
                fallback_response.suggested_actions,
            )
            ai_intent = self._normalize_intent(payload.get("intent")) or intent

            return EmployeeGuideResponse(
                answer=answer,
                steps=steps,
                formHelp=form_help,
                missingFields=missing_fields,
                prioritySuggestion=priority_suggestion,
                nextStepExplanation=next_step_explanation,
                suggestedActions=suggested_actions,
                severity=severity,
                intent=ai_intent,
                source="AI",
                available=True,
            )
        except ValidationError:
            return fallback_response

    def _sanitize_form_help(self, value: Any) -> list[EmployeeFormHelp]:
        items: list[EmployeeFormHelp] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:8]:
            if not isinstance(raw_item, dict):
                continue
            field = self._clean_text(raw_item.get("field"))
            help_text = self._clean_text(raw_item.get("help"))
            if not field or not help_text:
                continue
            items.append(EmployeeFormHelp(field=field, help=help_text))
        return items

    def _sanitize_missing_fields(self, value: Any) -> list[EmployeeMissingField]:
        items: list[EmployeeMissingField] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:8]:
            if not isinstance(raw_item, dict):
                continue
            field = self._clean_text(raw_item.get("field"))
            message = self._clean_text(raw_item.get("message"))
            if not field or not message:
                continue
            items.append(EmployeeMissingField(field=field, message=message))
        return items

    def _sanitize_priority_suggestion(self, value: Any) -> EmployeePrioritySuggestion | None:
        if not isinstance(value, dict):
            return None
        recommended_task_id = self._clean_text(value.get("recommendedTaskId")) or None
        reason = self._clean_text(value.get("reason"))
        if not reason:
            return None
        return EmployeePrioritySuggestion(
            recommendedTaskId=recommended_task_id,
            reason=reason,
        )

    def _sanitize_actions(self, value: Any) -> list[SuggestedAction]:
        items: list[SuggestedAction] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:8]:
            if not isinstance(raw_item, dict):
                continue
            action = self._clean_code(raw_item.get("action"))
            label = self._clean_text(raw_item.get("label"))
            if not action or not label:
                continue
            items.append(SuggestedAction(action=action, label=label))
        return items

    def _merge_actions(
        self,
        primary: list[SuggestedAction],
        fallback: list[SuggestedAction],
    ) -> list[SuggestedAction]:
        merged: list[SuggestedAction] = []
        seen: set[str] = set()
        for action in [*primary, *fallback]:
            if action.action in seen:
                continue
            seen.add(action.action)
            merged.append(action)
        return merged[:6]

    def _normalize_severity(self, value: Any) -> GuideSeverity | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        if normalized in GuideSeverity.__members__:
            return GuideSeverity[normalized]
        return None

    def _normalize_intent(self, value: Any) -> EmployeeGuideIntent | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        if normalized in EmployeeGuideIntent.__members__:
            return EmployeeGuideIntent[normalized]
        return None

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.strip().split())[:700]

    def _clean_code(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        normalized = "_".join(value.strip().upper().split())
        return normalized[:80]

    def _clean_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for raw_item in value[:5]:
            text = self._clean_text(raw_item)
            if text:
                items.append(text)
        return items

    guide_employee = guiar_funcionario


EmployeeGuideService = ServicioGuiaFuncionario
