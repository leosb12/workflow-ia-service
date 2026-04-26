import logging
import time
from typing import Any

from pydantic import ValidationError

from app.modules.guia_usuario.comun.solicitud_guia import SolicitudGuiaUsuarioMovil
from app.modules.guia_usuario.comun.respuesta_guia import (
    AccionSugerida,
    IntencionGuiaUsuarioMovil,
    RespuestaGuiaUsuarioMovil,
    SeveridadGuia,
)
from app.modules.guia_usuario.usuario_movil.clasificador_intencion_usuario_movil import (
    ClasificadorIntencionUsuarioMovil,
)
from app.modules.guia_usuario.usuario_movil.prompts_guia_usuario_movil import PromptsGuiaUsuarioMovil
from app.modules.guia_usuario.usuario_movil.respaldo_guia_usuario_movil import RespaldoGuiaUsuarioMovil
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class ServicioGuiaUsuarioMovil:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsGuiaUsuarioMovil,
        classifier: ClasificadorIntencionUsuarioMovil,
        fallback_service: RespaldoGuiaUsuarioMovil,
        llm_model: str,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts
        self.classifier = classifier
        self.fallback_service = fallback_service
        self.llm_model = llm_model

    async def guiar_usuario_movil(self, request: SolicitudGuiaUsuarioMovil) -> RespuestaGuiaUsuarioMovil:
        request_started_at = time.perf_counter()
        log.info("[TIMING][Guide] Inicio guide_mobile_user")

        intent_started_at = time.perf_counter()
        intent = self.classifier.detect(request.pregunta, request.pantalla)
        log.info(
            "[TIMING][Guide] detect mobile user intent en %.3fs intent=%s",
            time.perf_counter() - intent_started_at,
            intent.value,
        )

        fallback_started_at = time.perf_counter()
        fallback_response = self.fallback_service.build_response(request, intent)
        log.info(
            "[TIMING][Guide] build mobile user fallback en %.3fs",
            time.perf_counter() - fallback_started_at,
        )

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
                "[TIMING][Guide] mobile user run_json_prompt en %.3fs model=%s",
                time.perf_counter() - llm_started_at,
                self.llm_model,
            )

            parse_started_at = time.perf_counter()
            payload = self.json_parser.parse(raw_json)
            log.info(
                "[TIMING][Guide] mobile user json_parser.parse en %.3fs",
                time.perf_counter() - parse_started_at,
            )

            sanitize_started_at = time.perf_counter()
            response = self._sanitize_response(payload, fallback_response, intent)
            log.info(
                "[TIMING][Guide] mobile user sanitize_response en %.3fs",
                time.perf_counter() - sanitize_started_at,
            )
            log.info(
                "[TIMING][Guide] guide_mobile_user total en %.3fs source=%s",
                time.perf_counter() - request_started_at,
                response.fuente,
            )
            return response
        except Exception as exc:
            log.warning("No se pudo completar mobile user guide con IA. Se usa fallback: %s", exc)
            log.info(
                "[TIMING][Guide] guide_mobile_user total con fallback en %.3fs",
                time.perf_counter() - request_started_at,
            )
            return fallback_response

    def _sanitize_response(
        self,
        payload: dict[str, Any],
        fallback_response: RespuestaGuiaUsuarioMovil,
        intent: IntencionGuiaUsuarioMovil,
    ) -> RespuestaGuiaUsuarioMovil:
        try:
            respuesta = self._clean_text(payload.get("answer")) or fallback_response.respuesta
            pasos = self._clean_list(payload.get("steps")) or fallback_response.pasos
            estado_explicado = (
                self._clean_text(payload.get("estadoExplicado")) or fallback_response.estado_explicado
            )
            progreso_explicado = (
                self._clean_text(payload.get("progresoExplicado")) or fallback_response.progreso_explicado
            )
            documentos_faltantes = (
                self._clean_list(payload.get("documentosFaltantes")) or fallback_response.documentos_faltantes
            )
            proximos_pasos = (
                self._clean_list(payload.get("proximosPasos")) or fallback_response.proximos_pasos
            )
            acciones_sugeridas = self._merge_actions(
                self._sanitize_actions(payload.get("accionesSugeridas")),
                fallback_response.acciones_sugeridas,
            )
            severidad = self._normalize_severity(payload.get("severity")) or fallback_response.severidad
            ai_intent = self._normalize_intent(payload.get("intent")) or intent

            return RespuestaGuiaUsuarioMovil(
                respuesta=respuesta,
                pasos=pasos,
                estado_explicado=estado_explicado,
                progreso_explicado=progreso_explicado,
                documentos_faltantes=documentos_faltantes,
                proximos_pasos=proximos_pasos,
                acciones_sugeridas=acciones_sugeridas,
                severidad=severidad,
                intencion=ai_intent,
                fuente="AI",
                disponible=True,
            )
        except ValidationError:
            return fallback_response

    def _sanitize_actions(self, value: Any) -> list[AccionSugerida]:
        items: list[AccionSugerida] = []
        if not isinstance(value, list):
            return items
        for raw_item in value[:8]:
            if not isinstance(raw_item, dict):
                continue
            action = self._clean_code(raw_item.get("action"))
            label = self._clean_text(raw_item.get("label"))
            if not action or not label:
                continue
            items.append(AccionSugerida(action=action, label=label))
        return items

    def _merge_actions(
        self,
        primary: list[AccionSugerida],
        fallback: list[AccionSugerida],
    ) -> list[AccionSugerida]:
        merged: list[AccionSugerida] = []
        seen: set[str] = set()
        for action in [*primary, *fallback]:
            if action.action in seen:
                continue
            seen.add(action.action)
            merged.append(action)
        return merged[:5]

    def _normalize_severity(self, value: Any) -> SeveridadGuia | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        if normalized in SeveridadGuia.__members__:
            return SeveridadGuia[normalized]
        return None

    def _normalize_intent(self, value: Any) -> IntencionGuiaUsuarioMovil | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        if normalized in IntencionGuiaUsuarioMovil.__members__:
            return IntencionGuiaUsuarioMovil[normalized]
        return None

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return " ".join(value.strip().split())[:700]

    def _clean_code(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        return "_".join(value.strip().upper().split())[:80]

    def _clean_list(self, value: Any) -> list[str]:
        if not isinstance(value, list):
            return []
        items: list[str] = []
        for raw_item in value[:5]:
            text = self._clean_text(raw_item)
            if text:
                items.append(text)
        return items

    guide_mobile_user = guiar_usuario_movil


MobileUserGuideService = ServicioGuiaUsuarioMovil
