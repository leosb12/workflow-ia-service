import logging

import httpx
from fastapi import HTTPException

from app.core.config import Settings
from app.modules.clasificador_solicitudes_orquestador.modelos import (
    IaClasificacionRequest,
    IaClasificacionResponse,
)

log = logging.getLogger(__name__)


class ClienteDeepLearningClasificador:
    def __init__(self, settings: Settings) -> None:
        self.base_url = settings.ia_deep_learning_service_url.strip().rstrip("/")
        self.timeout = 30.0

    async def clasificar(self, request: IaClasificacionRequest, ai_mode: str | None = None) -> IaClasificacionResponse:
        url = f"{self.base_url}/api/deep-learning/clasificador-solicitudes/clasificar-dinamico"
        payload = request.model_dump(by_alias=True)
        headers = {}
        if ai_mode:
            headers["X-AI-Mode"] = ai_mode

        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(url, json=payload, headers=headers)
                response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            log.warning(
                "ia-deep-learning-service rechazo la clasificacion dinamica: status=%s body=%s",
                exc.response.status_code,
                exc.response.text[:1000],
            )
            raise HTTPException(
                status_code=503,
                detail={"error": "IA_DEEP_LEARNING_NO_DISPONIBLE"},
            ) from exc
        except httpx.HTTPError as exc:
            log.warning("ia-deep-learning-service no disponible: %s", exc)
            raise HTTPException(
                status_code=503,
                detail={"error": "IA_DEEP_LEARNING_NO_DISPONIBLE"},
            ) from exc

        return IaClasificacionResponse.model_validate(response.json())
