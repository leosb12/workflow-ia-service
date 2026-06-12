from app.modules.clasificador_solicitudes_orquestador.cliente_deep_learning import ClienteDeepLearningClasificador
from app.modules.clasificador_solicitudes_orquestador.modelos import (
    IaClasificacionRequest,
    IaClasificacionResponse,
)


class ServicioClasificadorSolicitudes:
    def __init__(self, cliente_deep_learning: ClienteDeepLearningClasificador) -> None:
        self.cliente_deep_learning = cliente_deep_learning

    async def clasificar(self, request: IaClasificacionRequest, ai_mode: str | None = None) -> IaClasificacionResponse:
        return await self.cliente_deep_learning.clasificar(request, ai_mode)
