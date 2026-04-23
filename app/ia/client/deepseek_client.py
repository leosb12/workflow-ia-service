import logging

import httpx
from starlette.status import HTTP_500_INTERNAL_SERVER_ERROR, HTTP_502_BAD_GATEWAY

from app.core.config import Settings
from app.core.exceptions import ApiException
from app.ia.dto.deepseek import DeepSeekMessage, DeepSeekRequest, DeepSeekResponse, ResponseFormat

log = logging.getLogger(__name__)


class DeepSeekClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

    async def generar_json(self, messages: list[DeepSeekMessage]) -> str:
        self._validar_configuracion()
        max_tokens = self.settings.deepseek_max_tokens if self.settings.deepseek_max_tokens > 0 else None
        timeout = self.settings.deepseek_timeout_seconds if self.settings.deepseek_timeout_seconds > 0 else None

        request = DeepSeekRequest(
            model=self.settings.deepseek_model.strip(),
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
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.post(
                    self.settings.deepseek_chat_completions_url,
                    headers=headers,
                    json=request.model_dump(by_alias=True, exclude_none=True),
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
            deepseek_response = DeepSeekResponse.model_validate(response.json())
        except ValueError as exc:
            log.warning("DeepSeek devolvio una respuesta no JSON: %s", exc)
            raise ApiException(HTTP_502_BAD_GATEWAY, "DeepSeek devolvio una respuesta invalida") from exc

        return self._extraer_contenido(deepseek_response)

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
