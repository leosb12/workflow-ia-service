from app.core.config import get_settings
from app.modules.clasificador_solicitudes_orquestador.cliente_deep_learning import ClienteDeepLearningClasificador
from app.modules.clasificador_solicitudes_orquestador.servicio import ServicioClasificadorSolicitudes


def obtener_servicio_clasificador_solicitudes() -> ServicioClasificadorSolicitudes:
    cliente = ClienteDeepLearningClasificador(settings=get_settings())
    return ServicioClasificadorSolicitudes(cliente_deep_learning=cliente)
