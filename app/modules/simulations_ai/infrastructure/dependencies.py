from app.modules.simulations_ai.prompts.simulation_prompts import SimulationPrompts
from app.modules.simulations_ai.service.simulations_ai_service import SimulationsAiService


def get_simulations_ai_service() -> SimulationsAiService:
    return SimulationsAiService(prompts=SimulationPrompts())
