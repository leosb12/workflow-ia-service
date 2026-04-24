from app.modules.simulations_ai.schemas.simulation_request import (
    SimulationAnalysisRequest,
    SimulationComparisonRequest,
)


class SimulationPrompts:
    """Placeholder prompt builder for future LLM-backed simulation analysis."""

    def build_analysis_system_prompt(self) -> str:
        return (
            "Eres un analista experto en simulaciones de politicas de negocio. "
            "Devuelve siempre JSON estructurado y recomendaciones profesionales."
        )

    def build_analysis_user_prompt(self, request: SimulationAnalysisRequest) -> str:
        return request.model_dump_json(by_alias=True, exclude_none=True)

    def build_comparison_system_prompt(self) -> str:
        return (
            "Eres un analista experto en comparacion de politicas simuladas. "
            "Devuelve siempre JSON estructurado y una conclusion clara."
        )

    def build_comparison_user_prompt(self, request: SimulationComparisonRequest) -> str:
        return request.model_dump_json(by_alias=True, exclude_none=True)
