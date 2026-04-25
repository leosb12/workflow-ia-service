from app.modules.generador_flujos.aplicacion.caso_uso_generar_flujo import (
    CasoUsoGenerarFlujo,
)


class IaService:
    def __init__(self, use_case: CasoUsoGenerarFlujo) -> None:
        self.use_case = use_case

    async def convertir_texto_a_flujo(self, request):
        return await self.use_case.ejecutar(request)
