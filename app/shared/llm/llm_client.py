import logging
import time

import httpx
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_502_BAD_GATEWAY

from app.core.config import Settings
from app.core.exceptions import ApiException
from app.shared.schemas.deepseek import (
    DeepSeekMessage,
    DeepSeekRequest,
    DeepSeekResponse,
    ResponseFormat,
)

log = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generar_json(
        self,
        messages: list[DeepSeekMessage],
        *,
        model_override: str | None = None,
    ) -> str:
        self._validar_configuracion()
        max_tokens = self.settings.deepseek_max_tokens if self.settings.deepseek_max_tokens > 0 else None
        timeout = self.settings.deepseek_timeout_seconds if self.settings.deepseek_timeout_seconds > 0 else None
        request_started_at = time.perf_counter()
        selected_model = (model_override or self.settings.deepseek_model).strip()

        request = DeepSeekRequest(
            model=selected_model,
            messages=messages,
            response_format=ResponseFormat(type="json_object"),
            max_tokens=max_tokens,
            temperature=self.settings.deepseek_temperature,
            stream=False,
        )

        headers = {
            "Authorization": f"Bearer {self.settings.deepseek_api_key.strip()}",
            "Content-Type": "application/json",
        }

        try:
            client_started_at = time.perf_counter()
            async with httpx.AsyncClient(timeout=timeout) as client:
                log.info(
                    "[TIMING][DeepSeek] AsyncClient listo en %.3fs",
                    time.perf_counter() - client_started_at,
                )
                http_started_at = time.perf_counter()
                response = await client.post(
                    self.settings.deepseek_chat_completions_url,
                    headers=headers,
                    json=request.model_dump(by_alias=True, exclude_none=True),
                )
                log.info(
                    "[TIMING][DeepSeek] POST completado en %.3fs status=%s model=%s",
                    time.perf_counter() - http_started_at,
                    response.status_code,
                    selected_model,
                )
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            status = exc.response.status_code
            log.warning("DeepSeek respondio HTTP %s: %s", status, self._safe_body(exc.response.text))
            raise ApiException(
                HTTP_502_BAD_GATEWAY,
                f"DeepSeek no pudo procesar la solicitud. Codigo HTTP: {status}",
            ) from exc
        except httpx.TimeoutException as exc:
            log.warning("Timeout llamando a DeepSeek: %s", exc)
            raise ApiException(HTTP_502_BAD_GATEWAY, "DeepSeek no respondio a tiempo") from exc
        except httpx.RequestError as exc:
            log.warning("No se pudo conectar con DeepSeek: %s", exc)
            raise ApiException(HTTP_502_BAD_GATEWAY, "No se pudo conectar con DeepSeek") from exc

        try:
            response_json_started_at = time.perf_counter()
            response_json = response.json()
            log.info(
                "[TIMING][DeepSeek] response.json() en %.3fs",
                time.perf_counter() - response_json_started_at,
            )

            validation_started_at = time.perf_counter()
            deepseek_response = DeepSeekResponse.model_validate(response_json)
            log.info(
                "[TIMING][DeepSeek] model_validate() en %.3fs",
                time.perf_counter() - validation_started_at,
            )
        except ValueError as exc:
            log.warning("DeepSeek devolvio una respuesta no JSON: %s", exc)
            raise ApiException(HTTP_502_BAD_GATEWAY, "DeepSeek devolvio una respuesta invalida") from exc

        extract_started_at = time.perf_counter()
        content = self._extraer_contenido(deepseek_response)
        log.info(
            "[TIMING][DeepSeek] extraccion de contenido en %.3fs",
            time.perf_counter() - extract_started_at,
        )
        log.info(
            "[TIMING][DeepSeek] generar_json total en %.3fs model=%s",
            time.perf_counter() - request_started_at,
            selected_model,
        )
        return content

    def _validar_configuracion(self) -> None:
        if not self.settings.deepseek_api_key.strip():
            raise ApiException(HTTP_500_INTERNAL_SERVER_ERROR, "DEEPSEEK_API_KEY no esta configurada")

        if not self.settings.deepseek_base_url.strip():
            raise ApiException(HTTP_500_INTERNAL_SERVER_ERROR, "DEEPSEEK_BASE_URL no esta configurada")

        if not self.settings.deepseek_model.strip():
            raise ApiException(HTTP_500_INTERNAL_SERVER_ERROR, "DEEPSEEK_MODEL no esta configurado")

    def _extraer_contenido(self, response: DeepSeekResponse) -> str:
        if not response.choices:
            raise ApiException(HTTP_502_BAD_GATEWAY, "DeepSeek no devolvio opciones de respuesta")

        choice = response.choices[0]
        if choice.finish_reason and choice.finish_reason.lower() == "length":
            log.warning("DeepSeek reporto finish_reason=length; se intentara parsear y corregir el contenido")

        if choice.message is None or not choice.message.content or not choice.message.content.strip():
            raise ApiException(HTTP_502_BAD_GATEWAY, "DeepSeek devolvio contenido vacio")

        return choice.message.content.strip()

    def _safe_body(self, body: str | None) -> str:
        if not body or not body.strip():
            return "<empty>"

        normalized = " ".join(body.split())
        return normalized if len(normalized) <= 500 else normalized[:500] + "..."
