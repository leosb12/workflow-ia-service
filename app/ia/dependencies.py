from app.ia.servicio.ia_service import IaService
from app.modules.generador_flujos.aplicacion.caso_uso_generar_flujo import (
    CasoUsoGenerarFlujo,
)
from app.modules.generador_flujos.infraestructura.dependencias import (
    obtener_caso_uso_generar_flujo,
)


def obtener_servicio_ia() -> IaService:
    return IaService(use_case=obtener_caso_uso_generar_flujo())


def obtener_servicio_generador_flujos() -> CasoUsoGenerarFlujo:
    return obtener_caso_uso_generar_flujo()


get_ia_service = obtener_servicio_ia
get_generate_workflow_service = obtener_servicio_generador_flujos
