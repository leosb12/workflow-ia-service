import logging
import time
from typing import Any

from pydantic import ValidationError

from app.modules.guia_usuario.administrador.respaldo_guia_administrador import (
    RespaldoGuiaAdministrador,
)
from app.modules.guia_usuario.administrador.clasificador_intencion_administrador import (
    ClasificadorIntencionAdministrador,
)
from app.modules.guia_usuario.administrador.prompts_guia_administrador import PromptsGuiaAdministrador
from app.modules.guia_usuario.comun.solicitud_guia import AdminGuideRequest
from app.modules.guia_usuario.comun.respuesta_guia import (
    AdminGuideIntent,
    AdminGuideResponse,
    GuideIssue,
    GuideSeverity,
    SuggestedAction,
    SuggestedFormField,
    SuggestedResponsible,
)
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class ServicioGuiaAdministrador:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsGuiaAdministrador,
        classifier: ClasificadorIntencionAdministrador,
        fallback_service: RespaldoGuiaAdministrador,
        llm_model: str,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts
        self.classifier = classifier
        self.fallback_service = fallback_service
        self.llm_model = llm_model

    async def guiar_administrador(self, request: AdminGuideRequest) -> AdminGuideResponse:
        request_started_at = time.perf_counter()
        log.info("[TIMING][Guide] Inicio guide_admin")

        intent_started_at = time.perf_counter()
        intent = self.classifier.detect(request.question, request.screen)
        log.info(
            "[TIMING][Guide] detect intent en %.3fs intent=%s",
            time.perf_counter() - intent_started_at,
            intent.value,
        )

        fallback_started_at = time.perf_counter()
        fallback_response = self.fallback_service.build_response(request, intent)
        log.info(
            "[TIMING][Guide] build fallback en %.3fs",
            time.perf_counter() - fallback_started_at,
        )

        if request.screen.name == "PERFIL_USUARIO":
            log.info(
                "[TIMING][Guide] admin profile screen usa fallback directo en %.3fs",
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
                "[TIMING][Guide] run_json_prompt en %.3fs model=%s",
                time.perf_counter() - llm_started_at,
                self.llm_model,
            )

            parse_started_at = time.perf_counter()
            payload = self.json_parser.parse(raw_json)
            log.info(
                "[TIMING][Guide] json_parser.parse en %.3fs",
                time.perf_counter() - parse_started_at,
            )

            sanitize_started_at = time.perf_counter()
            response = self._sanitize_response(payload, fallback_response, intent)
            log.info(
                "[TIMING][Guide] sanitize_response en %.3fs",
                time.perf_counter() - sanitize_started_at,
            )
            log.info(
                "[TIMING][Guide] guide_admin total en %.3fs source=%s",
                time.perf_counter() - request_started_at,
                response.source,
            )
            return response
        except Exception as exc:
            log.warning("No se pudo completar admin guide con IA. Se usa fallback: %s", exc)
            log.info(
                "[TIMING][Guide] guide_admin total con fallback en %.3fs",
                time.perf_counter() - request_started_at,
            )
            return fallback_response

    def _sanitize_response(
        self,
        payload: dict[str, Any],
        fallback_response: AdminGuideResponse,
        intent: AdminGuideIntent,
    ) -> AdminGuideResponse:
        try:
            answer = self._clean_text(payload.get("answer")) or fallback_response.answer
            steps = self._clean_list(payload.get("steps")) or fallback_response.steps
            severity = self._normalize_severity(payload.get("severity")) or fallback_response.severity

            suggested_responsible = self._sanitize_responsible(payload.get("suggestedResponsible"))
            if suggested_responsible is None:
                suggested_responsible = fallback_response.suggested_responsible

            suggested_form = self._sanitize_form(payload.get("suggestedForm"))
            if not suggested_form:
                suggested_form = fallback_response.suggested_form

            detected_issues = self._merge_issues(
                self._sanitize_issues(payload.get("detectedIssues")),
                fallback_response.detected_issues,
            )
            suggested_actions = self._merge_actions(
                self._sanitize_actions(payload.get("suggestedActions")),
                fallback_response.suggested_actions,
            )

            ai_intent = self._normalize_intent(payload.get("intent")) or intent

            return AdminGuideResponse(
                answer=answer,
                steps=steps,
                suggestedResponsible=suggested_responsible,
                suggestedForm=suggested_form,
                detectedIssues=detected_issues,
                suggestedActions=suggested_actions,
                severity=severity,
                intent=ai_intent,
                source="AI",
                available=True,
            )
        except ValidationError:
            return fallback_response

    def _sanitize_responsible(self, value: Any) -> SuggestedResponsible | None:
        if not isinstance(value, dict):
            return None
        name = self._clean_text(value.get("name"))
        reason = self._clean_text(value.get("reason"))
        if not name or not reason:
            return None
        return SuggestedResponsible(name=name, reason=reason)

    def _sanitize_form(self, value: Any) -> list[SuggestedFormField]:
        items: list[SuggestedFormField] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:6]:
            if not isinstance(raw_item, dict):
                continue
            label = self._clean_text(raw_item.get("label"))
            field_type = self._clean_type(raw_item.get("type"))
            if not label or not field_type:
                continue
            items.append(
                SuggestedFormField(
                    label=label,
                    type=field_type,
                    required=bool(raw_item.get("required", False)),
                )
            )
        return items

    def _sanitize_issues(self, value: Any) -> list[GuideIssue]:
        items: list[GuideIssue] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:8]:
            if not isinstance(raw_item, dict):
                continue
            issue_type = self._clean_code(raw_item.get("type"))
            message = self._clean_text(raw_item.get("message"))
            if not issue_type or not message:
                continue
            items.append(GuideIssue(type=issue_type, message=message))
        return items

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

    def _merge_issues(
        self,
        primary: list[GuideIssue],
        fallback: list[GuideIssue],
    ) -> list[GuideIssue]:
        merged: list[GuideIssue] = []
        seen: set[str] = set()
        for issue in [*primary, *fallback]:
            if issue.type in seen:
                continue
            seen.add(issue.type)
            merged.append(issue)
        return merged[:8]

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

    def _normalize_intent(self, value: Any) -> AdminGuideIntent | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        if normalized in AdminGuideIntent.__members__:
            return AdminGuideIntent[normalized]
        return None

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.strip().split())[:700]

    def _clean_type(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        normalized = value.strip().upper()
        allowed = {"TEXT", "TEXTAREA", "BOOLEAN", "NUMBER", "DATE", "FILE", "SELECT"}
        return normalized if normalized in allowed else ""

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

    guide_admin = guiar_administrador


AdminGuideService = ServicioGuiaAdministrador
