from app.modules.simulacion.prompts.prompts_simulacion import PromptsSimulacion
from app.modules.simulacion.servicio.servicio_simulacion import ServicioSimulacion


def obtener_servicio_simulacion() -> ServicioSimulacion:
    return ServicioSimulacion(prompts=PromptsSimulacion())


get_servicio_simulacion = obtener_servicio_simulacion
get_simulations_ai_service = obtener_servicio_simulacion
