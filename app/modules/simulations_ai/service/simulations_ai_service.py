from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from app.modules.simulations_ai.prompts.simulation_prompts import SimulationPrompts
from app.modules.simulations_ai.schemas.simulation_request import (
    SimulationAnalysisRequest,
    SimulationComparisonRequest,
    SimulationDecisionStat,
    SimulationNodeStat,
    SimulationResult,
)
from app.modules.simulations_ai.schemas.simulation_response import (
    SimulationAnalysisResponse,
    SimulationComparisonResponse,
)


@dataclass(slots=True)
class _PolicyScore:
    policy_id: str | None
    policy_name: str | None
    efficiency_score: float
    summary: str
    recommendations: list[str]
    issues: list[str]
    strengths: list[str]
    risks: list[str]
    bottlenecks: list[str]
    conclusion: str


@dataclass(slots=True)
class _ComparisonSnapshot:
    first_name: str
    second_name: str
    first_time: float
    second_time: float
    first_bottlenecks: int
    second_bottlenecks: int
    first_score: float
    second_score: float
    winner_id: str | None
    winner_name: str
    winner_is_first: bool
    winner_time: float
    winner_bottlenecks: int
    winner_score: float
    loser_name: str
    loser_time: float
    loser_bottlenecks: int
    loser_score: float
    faster_name: str
    faster_time: float
    faster_is_first: bool
    slower_name: str
    slower_time: float
    time_diff: float
    relative_gap: float
    bottleneck_diff: int
    score_diff: float


class SimulationsAiService:
    """Heuristic analyzer for policy simulations.

    The service is intentionally rule-based so the FastAPI endpoint works without
    requiring an external LLM provider. The prompt builder is injected to keep the
    structure ready for a future LLM-backed implementation.
    """

    def __init__(self, prompts: SimulationPrompts) -> None:
        self.prompts = prompts

    async def analyze(self, request: SimulationAnalysisRequest) -> SimulationAnalysisResponse:
        result = request.result or SimulationResult()
        policy_name = self._policy_name(request.policy)
        score = self._score_result(result, request.configuration.base_node_duration_hours)
        issues = self._build_detected_issues(result)
        recommendations = self._build_recommendations(result, issues)
        strengths = self._build_strengths(result)
        risks = self._build_risks(result, request.configuration)
        bottlenecks = self._build_bottleneck_labels(result)
        summary = self._build_analysis_summary(
            policy_name,
            result,
            bottlenecks,
            score,
            request.configuration,
        )
        conclusion = self._build_executive_conclusion(
            policy_name,
            score,
            issues,
            risks,
            result,
            request.configuration,
        )

        return SimulationAnalysisResponse(
            summary=summary,
            source="AI",
            available=True,
            recommendations=recommendations,
            detectedIssues=issues,
            strengths=strengths,
            risks=risks,
            bottlenecks=bottlenecks,
            efficiencyScore=score,
            executiveConclusion=conclusion,
        )

    async def compare(self, request: SimulationComparisonRequest) -> SimulationComparisonResponse:
        comparison = request.comparison
        if comparison is None:
            return SimulationComparisonResponse(
                summary="No se recibieron suficientes metricas para comparar las politicas simuladas.",
                source="AI",
                available=True,
                recommendations=[
                    "Enviar las metricas comparativas de ambas politicas para evaluar tiempos y cuellos de botella."
                ],
                detectedIssues=["La comparacion no incluyo el bloque comparison."],
                strengths=[],
                risks=["La ausencia de datos comparativos limita la conclusion."],
                efficiencyScore=None,
                executiveConclusion="Comparacion neutral por falta de datos comparativos completos.",
            )

        first_score = self._build_comparison_score(
            average_time=comparison.first_average_estimated_time_hours,
            bottleneck_count=comparison.first_bottleneck_count,
        )
        second_score = self._build_comparison_score(
            average_time=comparison.second_average_estimated_time_hours,
            bottleneck_count=comparison.second_bottleneck_count,
        )
        winner = self._resolve_winner(request, comparison, first_score, second_score)
        snapshot = self._build_comparison_snapshot(request, comparison, winner, first_score, second_score)
        neutral = self._is_neutral_comparison(snapshot)

        if neutral:
            summary = self._build_neutral_comparison_summary(snapshot)
        else:
            summary = self._build_comparison_summary(snapshot)

        recommendations = self._build_comparison_recommendations(snapshot, neutral)
        issues = self._build_comparison_issues(snapshot, neutral)
        strengths = self._build_comparison_strengths(snapshot, neutral)
        risks = self._build_comparison_risks(snapshot, neutral)
        conclusion = self._build_comparison_conclusion(snapshot, neutral)

        return SimulationComparisonResponse(
            summary=summary,
            source="AI",
            available=True,
            recommendations=recommendations,
            detectedIssues=issues,
            strengths=strengths,
            risks=risks,
            efficiencyScore=round(max(first_score, second_score), 2),
            executiveConclusion=conclusion,
            moreEfficientPolicyId=snapshot.winner_id,
            moreEfficientPolicyName=snapshot.winner_name,
        )

    def _policy_name(self, policy: Any) -> str:
        if policy is None:
            return "la politica analizada"
        name = getattr(policy, "nombre", None)
        policy_id = getattr(policy, "id", None)
        if isinstance(name, str) and name.strip():
            return name.strip()
        if isinstance(policy_id, str) and policy_id.strip():
            return policy_id.strip()
        return "la politica analizada"

    def _score_result(self, result: SimulationResult, base_node_duration_hours: float | None) -> float:
        average_time = self._safe_float(result.average_estimated_time_hours)
        highest_load = self._safe_float(result.highest_load_percentage)
        bottleneck_count = len(self._non_empty_values(result.bottleneck_node_ids))
        warnings_penalty = min(12.0, len(self._non_empty_values(result.warnings)) * 2.5)
        base_penalty = self._safe_float(base_node_duration_hours) * 4 if base_node_duration_hours else 0.0

        score = 100.0
        score -= average_time * 8.0
        score -= highest_load * 0.35
        score -= bottleneck_count * 6.0
        score -= warnings_penalty
        score -= base_penalty
        return round(max(0.0, min(100.0, score)), 2)

    def _build_detected_issues(self, result: SimulationResult) -> list[str]:
        issues: list[str] = []

        highest_load = self._safe_float(result.highest_load_percentage)
        highest_load_name = self._choose_name(
            result.highest_load_node_name,
            result.highest_load_node_id,
            "un nodo con alta carga",
        )
        if highest_load >= 35:
            issues.append(
                f"El nodo {highest_load_name} concentra {self._format_percent(highest_load)} de la carga total; si esta etapa se demora, arrastra el resto del flujo."
            )

        bottleneck_names = self._non_empty_values(result.bottleneck_node_names)
        bottleneck_ids = self._non_empty_values(result.bottleneck_node_ids)
        bottlenecks = bottleneck_names or bottleneck_ids
        if len(bottlenecks) >= 2:
            issues.append(
                "Se identificaron varios cuellos de botella potenciales en "
                + self._join_labels(bottlenecks[:3])
                + ", lo que sugiere esperas encadenadas entre etapas."
            )
        elif len(bottlenecks) == 1:
            issues.append(
                f"El principal cuello de botella aparece en {bottlenecks[0]}, punto que merece una revision operativa detallada."
            )

        average_time = self._safe_float(result.average_estimated_time_hours)
        if average_time >= 6:
            issues.append(
                f"El tiempo promedio estimado por instancia es alto ({self._format_hours(average_time)} h), por lo que el flujo puede comprometer tiempos de atencion y niveles de servicio."
            )

        for node in self._top_nodes(result.node_stats, limit=2):
            load = self._safe_float(node.load_percentage)
            average_node_time = self._safe_float(node.average_estimated_time_hours)
            if load >= 25 or average_node_time >= 2:
                name = self._choose_name(node.node_name, node.node_id, "un nodo")
                issues.append(
                    f"{name} registra {self._safe_int(node.executions)} ejecuciones, {self._format_percent(load)} de carga y {self._format_hours(average_node_time)} h promedio por caso."
                )

        for decision in result.decision_stats:
            issue = self._decision_imbalance_issue(decision)
            if issue:
                issues.append(issue)

        for warning in self._non_empty_values(result.warnings):
            issues.append(f"Advertencia del motor de simulacion: {warning}.")

        return self._deduplicate(issues)[:6]

    def _build_recommendations(self, result: SimulationResult, issues: list[str]) -> list[str]:
        recommendations: list[str] = []
        highest_load = self._safe_float(result.highest_load_percentage)
        highest_load_name = self._choose_name(
            result.highest_load_node_name,
            result.highest_load_node_id,
            "el nodo mas cargado",
        )
        bottlenecks = self._build_bottleneck_labels(result)
        average_time = self._safe_float(result.average_estimated_time_hours)

        if highest_load >= 35:
            recommendations.append(
                f"Descongestionar {highest_load_name} redistribuyendo carga, automatizando tareas repetitivas o dividiendo esa etapa en actividades mas cortas."
            )

        for bottleneck in bottlenecks[:2]:
            recommendations.append(
                f"Revisar {bottleneck} paso a paso para identificar aprobaciones, validaciones o esperas que puedan eliminarse o ejecutarse en paralelo."
            )

        if result.decision_stats:
            for detail in self._build_decision_breakdown(result, limit=1):
                recommendations.append(
                    "Validar las reglas de decision asociadas a este patron: "
                    + detail
                )

        if average_time >= 6:
            recommendations.append(
                f"Reducir las duraciones acumuladas del flujo, porque hoy cada instancia tarda {self._format_hours(average_time)} h en promedio."
            )

        if result.warnings:
            recommendations.append("Reproducir y revisar las advertencias del motor de simulacion antes de escalar el flujo a mas volumen.")

        if not recommendations:
            recommendations.append(
                "Mantener la configuracion actual y seguir monitoreando tiempos, carga y decisiones para confirmar que el comportamiento se mantiene estable."
            )

        if issues and len(recommendations) < 4:
            recommendations.append("Validar estos hallazgos con una segunda simulacion ajustando duraciones o reglas de decision.")

        return self._deduplicate(recommendations)[:6]

    def _build_strengths(self, result: SimulationResult) -> list[str]:
        strengths: list[str] = []
        highest_load = self._safe_float(result.highest_load_percentage)
        bottleneck_count = len(self._non_empty_values(result.bottleneck_node_ids))

        if highest_load < 30 and highest_load > 0:
            strengths.append(
                f"La carga maxima se mantiene en {self._format_percent(highest_load)}, lo que indica una distribucion relativamente sana entre nodos."
            )

        if bottleneck_count <= 1:
            strengths.append(
                f"La cantidad de cuellos de botella aparentes es baja ({bottleneck_count}), lo que reduce el riesgo de bloqueos estructurales."
            )

        if not result.decision_stats:
            strengths.append("No se detectaron decisiones complejas que agreguen variabilidad fuerte al flujo.")

        if not result.warnings:
            strengths.append("La corrida no reporto advertencias tecnicas del motor de simulacion.")

        if self._safe_int(result.instances_simulated) >= 100:
            strengths.append(
                f"La simulacion se apoyo en {self._safe_int(result.instances_simulated)} instancias, suficiente para observar patrones iniciales con algo de estabilidad."
            )

        if not strengths:
            strengths.append("La simulacion presenta suficiente estructura para continuar con mejoras graduales.")

        return self._deduplicate(strengths)[:5]

    def _build_risks(self, result: SimulationResult, configuration: Any) -> list[str]:
        risks: list[str] = []
        highest_load = self._safe_float(result.highest_load_percentage)
        highest_load_name = self._choose_name(
            result.highest_load_node_name,
            result.highest_load_node_id,
            "el nodo mas cargado",
        )
        average_time = self._safe_float(result.average_estimated_time_hours)
        bottlenecks = self._build_bottleneck_labels(result)

        if highest_load >= 40:
            risks.append(
                f"Existe riesgo de acumulacion en {highest_load_name}, porque ya absorbe {self._format_percent(highest_load)} de la carga total."
            )

        if len(bottlenecks) >= 2:
            risks.append(
                "Varios cuellos de botella pueden amplificar la lentitud del proceso: "
                + self._join_labels(bottlenecks[:3])
                + "."
            )

        variability = self._safe_float(getattr(configuration, "variability_percent", None))
        if variability >= 25:
            risks.append(
                f"La variabilidad configurada es alta ({self._format_percent(variability)}) y puede ampliar la dispersion real de tiempos."
            )

        if average_time >= 6:
            risks.append(
                f"El tiempo promedio estimado de {self._format_hours(average_time)} h puede afectar los niveles de servicio esperados."
            )

        if result.warnings:
            risks.append("Las advertencias del motor de simulacion reducen la confianza operativa de la corrida.")

        return self._deduplicate(risks)[:5]

    def _build_bottleneck_labels(self, result: SimulationResult) -> list[str]:
        labels = self._non_empty_values(result.bottleneck_node_names)
        if labels:
            return labels[:5]
        return [label for label in self._non_empty_values(result.bottleneck_node_ids)[:5]]

    def _build_analysis_summary(
        self,
        policy_name: str,
        result: SimulationResult,
        bottlenecks: list[str],
        score: float,
        configuration: Any,
    ) -> str:
        points: list[str] = []
        instances = self._safe_int(result.instances_simulated)
        total_time = self._safe_float(result.total_estimated_time_hours)
        average_time = self._safe_float(result.average_estimated_time_hours)
        highest_load = self._safe_float(result.highest_load_percentage)
        highest_load_name = self._choose_name(
            result.highest_load_node_name,
            result.highest_load_node_id,
            "el nodo mas cargado",
        )
        top_nodes = self._top_nodes(result.node_stats, limit=2)
        decision_breakdown = self._build_decision_breakdown(result, limit=2)
        warnings = self._non_empty_values(result.warnings)
        variability = self._safe_float(getattr(configuration, "variability_percent", None))
        base_duration = self._safe_float(getattr(configuration, "base_node_duration_hours", None))

        if instances or total_time:
            points.append(
                f"Volumen analizado de {policy_name}: {instances} instancias simuladas con {self._format_hours(total_time)} h totales estimadas."
            )

        points.append(
            f"Tiempo promedio por caso: {self._format_hours(average_time)} h; esta es la referencia principal del costo operativo esperado para cada instancia."
        )
        points.append(
            f"Carga maxima: {highest_load_name} concentra {self._format_percent(highest_load)} de la carga, por lo que hoy es el punto mas sensible del flujo."
        )

        if top_nodes:
            points.append(
                "Detalle por nodos mas exigidos: "
                + "; ".join(self._describe_node_load(node) for node in top_nodes)
                + "."
            )

        if bottlenecks:
            points.append(
                "Cuellos de botella identificados uno por uno: "
                + self._join_labels(bottlenecks[:4])
                + "."
            )

        if decision_breakdown:
            points.append("Lectura de decisiones: " + " ".join(decision_breakdown))

        if warnings:
            points.append("Alertas tecnicas detectadas: " + "; ".join(warnings[:2]) + ".")

        if base_duration or variability:
            config_parts: list[str] = []
            if base_duration:
                config_parts.append(f"tiempo base de {self._format_hours(base_duration)} h por paso")
            if variability:
                config_parts.append(f"variabilidad estimada de {self._format_percent(variability)}")
            points.append("Configuracion de la corrida: " + " y ".join(config_parts) + ".")

        points.append(
            f"Lectura global final: el comportamiento general del flujo se ve {self._score_label(score)} para la configuracion simulada."
        )

        return self._truncate(self._compose_numbered_points(points), 1600)

    def _build_executive_conclusion(
        self,
        policy_name: str,
        score: float,
        issues: list[str],
        risks: list[str],
        result: SimulationResult,
        configuration: Any,
    ) -> str:
        highest_load_name = self._choose_name(
            result.highest_load_node_name,
            result.highest_load_node_id,
            "el nodo mas cargado",
        )
        bottlenecks = self._build_bottleneck_labels(result)
        variability = self._safe_float(getattr(configuration, "variability_percent", None))
        priorities: list[str] = []

        if self._safe_float(result.highest_load_percentage) >= 35:
            priorities.append(f"descongestionar {highest_load_name}")
        if bottlenecks:
            priorities.append("revisar " + self._join_labels(bottlenecks[:3]))
        if self._safe_float(result.average_estimated_time_hours) >= 6:
            priorities.append("reducir duraciones acumuladas del flujo")
        if result.decision_stats:
            priorities.append("validar reglas de decision dominantes")

        if score >= 78 and not risks:
            text = (
                f"{policy_name} muestra un desempeno saludable y, con base en esta corrida, no presenta riesgos estructurales fuertes."
            )
        elif score >= 60:
            text = (
                f"{policy_name} es funcional, pero el analisis senala focos concretos de mejora antes de escalar volumen."
            )
        else:
            text = (
                f"{policy_name} necesita ajustes relevantes antes de ampliarse, porque la corrida evidencia friccion operativa y tiempos acumulados altos."
            )

        if priorities:
            text += " Prioridades inmediatas: " + ", ".join(priorities[:4]) + "."
        if variability >= 25:
            text += f" La variabilidad del {self._format_percent(variability)} obliga a validar estos resultados con otra corrida."
        if issues:
            text += " Los hallazgos detallados deben revisarse uno por uno con el equipo funcional para confirmar causas reales."
        return self._truncate(text, 1200)

    def _build_comparison_score(self, *, average_time: float | None, bottleneck_count: int | None) -> float:
        avg = self._safe_float(average_time)
        bottlenecks = self._safe_int(bottleneck_count)
        score = 100.0 - avg * 10.0 - bottlenecks * 8.0
        return round(max(0.0, min(100.0, score)), 2)

    def _resolve_winner(
        self,
        request: SimulationComparisonRequest,
        comparison: Any,
        first_score: float,
        second_score: float,
    ) -> tuple[str | None, str | None]:
        if comparison.more_efficient_policy_id and comparison.more_efficient_policy_name:
            return comparison.more_efficient_policy_id, comparison.more_efficient_policy_name

        if first_score == second_score:
            return self._policy_id(request.first_policy), self._policy_name(request.first_policy)

        if second_score > first_score:
            return self._policy_id(request.second_policy), self._policy_name(request.second_policy)

        return self._policy_id(request.first_policy), self._policy_name(request.first_policy)

    def _build_comparison_snapshot(
        self,
        request: SimulationComparisonRequest,
        comparison: Any,
        winner: tuple[str | None, str | None],
        first_score: float,
        second_score: float,
    ) -> _ComparisonSnapshot:
        first_name = self._policy_name(request.first_policy)
        second_name = self._policy_name(request.second_policy)
        first_time = self._safe_float(comparison.first_average_estimated_time_hours)
        second_time = self._safe_float(comparison.second_average_estimated_time_hours)
        first_bottlenecks = self._safe_int(comparison.first_bottleneck_count)
        second_bottlenecks = self._safe_int(comparison.second_bottleneck_count)
        time_diff = abs(first_time - second_time)
        if not time_diff and comparison.average_time_difference_hours is not None:
            time_diff = abs(self._safe_float(comparison.average_time_difference_hours))

        positive_times = [value for value in [first_time, second_time] if value > 0]
        faster_time = min(positive_times) if positive_times else 0.0
        slower_time = max(positive_times) if positive_times else 0.0
        faster_is_first = first_time <= second_time if positive_times else True
        faster_name = first_name if faster_is_first else second_name
        slower_name = second_name if faster_is_first else first_name
        relative_gap = (time_diff / faster_time) if faster_time > 0 else 0.0

        first_policy_id = self._policy_id(request.first_policy)
        second_policy_id = self._policy_id(request.second_policy)
        if winner[0] == second_policy_id:
            winner_is_first = False
        elif winner[0] == first_policy_id:
            winner_is_first = True
        else:
            winner_is_first = first_score >= second_score

        winner_name = winner[1] or (first_name if winner_is_first else second_name)
        loser_name = second_name if winner_is_first else first_name
        winner_time = first_time if winner_is_first else second_time
        loser_time = second_time if winner_is_first else first_time
        winner_bottlenecks = first_bottlenecks if winner_is_first else second_bottlenecks
        loser_bottlenecks = second_bottlenecks if winner_is_first else first_bottlenecks
        winner_score = first_score if winner_is_first else second_score
        loser_score = second_score if winner_is_first else first_score

        return _ComparisonSnapshot(
            first_name=first_name,
            second_name=second_name,
            first_time=first_time,
            second_time=second_time,
            first_bottlenecks=first_bottlenecks,
            second_bottlenecks=second_bottlenecks,
            first_score=first_score,
            second_score=second_score,
            winner_id=winner[0],
            winner_name=winner_name,
            winner_is_first=winner_is_first,
            winner_time=winner_time,
            winner_bottlenecks=winner_bottlenecks,
            winner_score=winner_score,
            loser_name=loser_name,
            loser_time=loser_time,
            loser_bottlenecks=loser_bottlenecks,
            loser_score=loser_score,
            faster_name=faster_name,
            faster_time=faster_time,
            faster_is_first=faster_is_first,
            slower_name=slower_name,
            slower_time=slower_time,
            time_diff=time_diff,
            relative_gap=relative_gap,
            bottleneck_diff=abs(first_bottlenecks - second_bottlenecks),
            score_diff=abs(first_score - second_score),
        )

    def _build_neutral_comparison_summary(self, snapshot: _ComparisonSnapshot) -> str:
        points = self._build_comparison_base_points(snapshot)
        points.append(
            "Lectura comparativa: la brecha observada es reducida y no alcanza para declarar una ganadora robusta sin considerar costos de implementacion, reglas de negocio o una nueva corrida."
        )
        return self._truncate(self._compose_numbered_points(points), 1600)

    def _build_comparison_summary(self, snapshot: _ComparisonSnapshot) -> str:
        points = self._build_comparison_base_points(snapshot)
        points.append(self._build_winner_reason(snapshot))
        return self._truncate(self._compose_numbered_points(points), 1600)

    def _build_comparison_conclusion(self, snapshot: _ComparisonSnapshot, neutral: bool) -> str:
        if neutral:
            text = (
                f"No hay una ventaja operativa contundente: la diferencia es de {self._format_hours(snapshot.time_diff)} h por instancia, "
                f"equivalente a {self._format_percent(snapshot.relative_gap * 100)} sobre la politica mas rapida."
            )
            if snapshot.bottleneck_diff == 0:
                text += " Ambas politicas muestran la misma cantidad de cuellos de botella, por lo que la decision final depende de criterios adicionales."
            return self._truncate(text, 1200)

        text = f"{snapshot.winner_name} es la alternativa mas conveniente en esta corrida."
        if snapshot.winner_name == snapshot.faster_name and snapshot.faster_time > 0:
            text += (
                f" Reduce el tiempo promedio de {snapshot.loser_name} de {self._format_hours(snapshot.loser_time)} h "
                f"a {self._format_hours(snapshot.winner_time)} h, una mejora de {self._format_hours(snapshot.time_diff)} h por instancia."
            )
        else:
            text += (
                f" Aunque no es la politica mas rapida en tiempo puro, compensa con una estructura operativa mas estable."
            )

        if snapshot.bottleneck_diff == 0 and snapshot.time_diff >= 1:
            text += (
                " Como ambas politicas tienen la misma cantidad de cuellos de botella, la diferencia apunta a duraciones acumuladas mas largas o reglas menos eficientes en la alternativa mas lenta."
            )
        elif snapshot.winner_bottlenecks < snapshot.loser_bottlenecks:
            text += (
                f" Tambien mejora la estructura del flujo al pasar de {snapshot.loser_bottlenecks} a {snapshot.winner_bottlenecks} cuellos de botella."
            )

        text += " Esta lectura conviene validarla con una corrida adicional antes de tomar una decision definitiva."
        return self._truncate(text, 1200)

    def _build_comparison_recommendations(
        self,
        snapshot: _ComparisonSnapshot,
        neutral: bool,
    ) -> list[str]:
        recommendations: list[str] = [
            "Ejecutar una segunda corrida con otra semilla para confirmar que la ventaja observada se mantiene.",
        ]

        if neutral:
            recommendations.append(
                "Como la diferencia es acotada, complementar la decision con criterios de negocio como costo de implementacion, complejidad y facilidad de mantenimiento."
            )
            recommendations.append(
                "Comparar mas escenarios de volumen o variabilidad antes de adoptar una politica definitiva."
            )
            return self._deduplicate(recommendations)

        recommendations.append(
            f"Tomar a {snapshot.winner_name} como referencia para la siguiente iteracion, porque hoy ofrece mejor equilibrio entre tiempo promedio y estabilidad."
        )

        if snapshot.bottleneck_diff == 0 and snapshot.time_diff >= 1:
            recommendations.append(
                f"Revisar duraciones, reglas o actividades de {snapshot.loser_name}, ya que la brecha no se explica por cantidad de cuellos de botella sino por tiempo acumulado."
            )
        elif snapshot.loser_bottlenecks > snapshot.winner_bottlenecks:
            recommendations.append(
                f"Reducir los cuellos de botella de {snapshot.loser_name}, que hoy registra {snapshot.loser_bottlenecks} frente a {snapshot.winner_bottlenecks} de {snapshot.winner_name}."
            )

        if snapshot.relative_gap >= 0.5:
            recommendations.append(
                f"No escalar {snapshot.loser_name} sin ajustes, porque tarda {self._format_percent(snapshot.relative_gap * 100)} mas que la alternativa mas rapida."
            )

        return self._deduplicate(recommendations)[:5]

    def _build_comparison_issues(
        self,
        snapshot: _ComparisonSnapshot,
        neutral: bool,
    ) -> list[str]:
        issues: list[str] = []

        if neutral:
            issues.append(
                f"La brecha de tiempo entre {snapshot.first_name} y {snapshot.second_name} es reducida ({self._format_hours(snapshot.time_diff)} h), por lo que el resultado puede variar con otra corrida."
            )
        else:
            issues.append(
                f"{snapshot.loser_name} tarda {self._format_hours(snapshot.time_diff)} h mas por instancia que {snapshot.winner_name}, lo que representa una desventaja operativa clara."
            )

        if snapshot.bottleneck_diff == 0 and snapshot.time_diff >= 1:
            issues.append(
                "La misma cantidad de cuellos de botella no implica el mismo rendimiento: la diferencia real aparece en la duracion acumulada de actividades."
            )
        elif snapshot.loser_bottlenecks >= 3:
            issues.append(
                f"{snapshot.loser_name} presenta una cantidad relevante de cuellos de botella ({snapshot.loser_bottlenecks}), senal de congestion estructural."
            )

        return self._deduplicate(issues)[:5]

    def _build_comparison_strengths(
        self,
        snapshot: _ComparisonSnapshot,
        neutral: bool,
    ) -> list[str]:
        strengths: list[str] = [
            "La comparacion ofrece una lectura directa de tiempos y cuellos de botella para ambas politicas.",
        ]

        if neutral:
            strengths.append(
                "Ambas politicas se comportan de forma consistente bajo la misma configuracion, lo que permite comparar con una base comun."
            )
        else:
            strengths.append(
                f"{snapshot.winner_name} muestra la mejor combinacion disponible de tiempo promedio ({self._format_hours(snapshot.winner_time)} h) y estructura operativa para esta corrida."
            )

        if snapshot.bottleneck_diff == 0 and snapshot.time_diff >= 1:
            strengths.append(
                "La comparacion permite separar problemas de tiempo de problemas de congestion: aqui la diferencia esta en duraciones, no en cantidad de cuellos."
            )
        elif snapshot.bottleneck_diff > 0:
            strengths.append(
                "La diferencia de cuellos de botella ayuda a identificar cual politica tiene una estructura operativa mas liviana."
            )

        return self._deduplicate(strengths)[:5]

    def _build_comparison_risks(
        self,
        snapshot: _ComparisonSnapshot,
        neutral: bool,
    ) -> list[str]:
        risks: list[str] = []

        if neutral:
            risks.append(
                "La cercania entre ambas politicas puede hacer que la decision cambie con pequenas variaciones en la simulacion."
            )

        if snapshot.time_diff >= 1.5:
            risks.append(
                f"La politica mas lenta ({snapshot.slower_name}) puede amplificar tiempos de ciclo y demoras de atencion."
            )

        if snapshot.bottleneck_diff == 0 and snapshot.time_diff >= 1:
            risks.append(
                "Si no se revisan las duraciones internas, una politica puede seguir siendo mucho mas lenta aunque tenga el mismo numero de cuellos de botella."
            )
        elif max(snapshot.first_bottlenecks, snapshot.second_bottlenecks) >= 3:
            risks.append(
                "La politica con mayor cantidad de cuellos de botella puede requerir ajustes estructurales antes de escalar."
            )

        return self._deduplicate(risks)[:5]

    def _build_comparison_base_points(self, snapshot: _ComparisonSnapshot) -> list[str]:
        points = [
            f"{snapshot.first_name}: tiempo promedio {self._format_hours(snapshot.first_time)} h y {snapshot.first_bottlenecks} cuello(s) de botella.",
            f"{snapshot.second_name}: tiempo promedio {self._format_hours(snapshot.second_time)} h y {snapshot.second_bottlenecks} cuello(s) de botella.",
        ]

        if snapshot.time_diff > 0:
            points.append(
                f"La brecha de tiempo es de {self._format_hours(snapshot.time_diff)} h por instancia, equivalente a {self._format_percent(snapshot.relative_gap * 100)} sobre la politica mas rapida."
            )
        else:
            points.append("No se observa brecha de tiempo medible entre ambas politicas en esta corrida.")

        if snapshot.bottleneck_diff == 0:
            points.append(
                f"Ambas muestran {snapshot.first_bottlenecks} cuello(s) de botella; por eso la diferencia se explica mas por duraciones acumuladas que por cantidad de puntos criticos."
            )
        else:
            lower_name = snapshot.first_name if snapshot.first_bottlenecks < snapshot.second_bottlenecks else snapshot.second_name
            lower_count = min(snapshot.first_bottlenecks, snapshot.second_bottlenecks)
            points.append(
                f"La diferencia de cuellos de botella es de {snapshot.bottleneck_diff}; {lower_name} tiene la estructura mas liviana con {lower_count} punto(s) critico(s)."
            )

        return points

    def _build_winner_reason(self, snapshot: _ComparisonSnapshot) -> str:
        reasons: list[str] = []

        if snapshot.winner_name == snapshot.faster_name and snapshot.winner_time > 0:
            reasons.append(
                f"menor tiempo promedio ({self._format_hours(snapshot.winner_time)} h frente a {self._format_hours(snapshot.loser_time)} h)"
            )
        if snapshot.winner_bottlenecks < snapshot.loser_bottlenecks:
            reasons.append(
                f"menos cuellos de botella ({snapshot.winner_bottlenecks} frente a {snapshot.loser_bottlenecks})"
            )
        elif snapshot.winner_bottlenecks == snapshot.loser_bottlenecks and snapshot.time_diff >= 1:
            reasons.append("la misma cantidad de cuellos, pero con una ejecucion acumulada mucho mas rapida")

        if not reasons:
            reasons.append("mejor equilibrio general entre tiempo y estructura del flujo")

        return f"Lectura comparativa final: {snapshot.winner_name} se posiciona mejor por " + " y ".join(reasons) + "."

    def _decision_imbalance_issue(self, decision: SimulationDecisionStat) -> str | None:
        if not decision.outcomes or decision.total_decisions is None:
            return None
        total = self._safe_int(decision.total_decisions)
        if total <= 0:
            return None
        dominant_label, dominant_count = max(decision.outcomes.items(), key=lambda item: item[1])
        if dominant_count / total < 0.75:
            return None
        node_name = self._choose_name(decision.node_name, decision.node_id, "una decision")
        return (
            f"La decision {node_name} esta muy desbalanceada hacia '{dominant_label}' "
            f"({dominant_count}/{total} casos)."
        )

    def _build_decision_breakdown(
        self,
        result: SimulationResult,
        limit: int = 2,
    ) -> list[str]:
        details: list[str] = []

        for decision in result.decision_stats[:limit]:
            if not decision.outcomes or decision.total_decisions is None:
                continue

            total = self._safe_int(decision.total_decisions)
            if total <= 0:
                continue

            dominant_label, dominant_count = max(decision.outcomes.items(), key=lambda item: item[1])
            ratio = dominant_count / total
            node_name = self._choose_name(decision.node_name, decision.node_id, "una decision clave")
            percent = self._format_percent(ratio * 100)

            if ratio >= 0.75:
                details.append(
                    f"{node_name} envia {percent} de los casos a '{dominant_label}' ({dominant_count}/{total}), por lo que una sola ruta domina la mayor parte del flujo."
                )
            elif ratio >= 0.55:
                details.append(
                    f"{node_name} concentra {percent} en '{dominant_label}' ({dominant_count}/{total}), con una tendencia marcada aunque no absoluta."
                )
            else:
                details.append(
                    f"{node_name} reparte los casos con mayor equilibrio; la salida principal apenas alcanza {percent} ({dominant_count}/{total})."
                )

        return details

    def _top_nodes(self, node_stats: list[SimulationNodeStat], limit: int = 3) -> list[SimulationNodeStat]:
        filtered = [node for node in node_stats if node.load_percentage is not None]
        return sorted(filtered, key=lambda item: self._safe_float(item.load_percentage), reverse=True)[:limit]

    def _describe_node_load(self, node: SimulationNodeStat) -> str:
        name = self._choose_name(node.node_name, node.node_id, "un nodo")
        load = self._safe_float(node.load_percentage)
        average_time = self._safe_float(node.average_estimated_time_hours)
        executions = self._safe_int(node.executions)
        details: list[str] = []

        if load:
            details.append(f"{self._format_percent(load)} de carga")
        if average_time:
            details.append(f"{self._format_hours(average_time)} h promedio")
        if executions:
            details.append(f"{executions} ejecuciones")

        if not details:
            return name
        if len(details) == 1:
            return f"{name} con {details[0]}"
        return f"{name} con " + ", ".join(details[:-1]) + f" y {details[-1]}"

    def _score_label(self, score: float) -> str:
        if score >= 80:
            return "saludable"
        if score >= 60:
            return "estable pero con alertas puntuales"
        if score >= 40:
            return "exigido y con necesidad de mejoras"
        return "fragil y con necesidad de ajustes relevantes"

    def _compose_numbered_points(self, values: list[str]) -> str:
        cleaned = [value.strip() for value in values if isinstance(value, str) and value.strip()]
        return " ".join(f"{index}. {value}" for index, value in enumerate(cleaned, start=1))

    def _choose_name(self, name: str | None, fallback: str | None, default: str) -> str:
        if isinstance(name, str) and name.strip():
            return name.strip()
        if isinstance(fallback, str) and fallback.strip():
            return fallback.strip()
        return default

    def _policy_id(self, policy: Any) -> str | None:
        value = getattr(policy, "id", None) if policy is not None else None
        return value if isinstance(value, str) and value.strip() else None

    def _format_hours(self, value: float) -> str:
        return f"{value:.2f}".rstrip("0").rstrip(".") if value else "0"

    def _format_percent(self, value: float) -> str:
        return f"{value:.1f}".rstrip("0").rstrip(".") + "%"

    def _safe_float(self, value: Any) -> float:
        try:
            if value is None:
                return 0.0
            return float(value)
        except (TypeError, ValueError):
            return 0.0

    def _safe_int(self, value: Any) -> int:
        try:
            if value is None:
                return 0
            return int(value)
        except (TypeError, ValueError):
            return 0

    def _non_empty_values(self, values: Any) -> list[str]:
        if not isinstance(values, list):
            return []
        return [value.strip() for value in values if isinstance(value, str) and value.strip()]

    def _deduplicate(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        unique: list[str] = []
        for value in values:
            cleaned = value.strip()
            if cleaned and cleaned not in seen:
                seen.add(cleaned)
                unique.append(cleaned)
        return unique

    def _truncate(self, text: str, limit: int) -> str:
        cleaned = " ".join(text.split())
        return cleaned if len(cleaned) <= limit else cleaned[: limit - 3].rstrip() + "..."

    def _counts_close(self, first: int | None, second: int | None) -> bool:
        return abs(self._safe_int(first) - self._safe_int(second)) <= 1

    def _is_neutral_comparison(self, snapshot: _ComparisonSnapshot) -> bool:
        return (
            self._counts_close(snapshot.first_bottlenecks, snapshot.second_bottlenecks)
            and snapshot.time_diff <= 0.5
            and snapshot.relative_gap <= 0.1
            and snapshot.score_diff <= 8.0
        )

    def _join_labels(self, values: list[str]) -> str:
        cleaned = [value for value in values if value]
        if not cleaned:
            return ""
        if len(cleaned) == 1:
            return cleaned[0]
        if len(cleaned) == 2:
            return f"{cleaned[0]} y {cleaned[1]}"
        return ", ".join(cleaned[:-1]) + f" y {cleaned[-1]}"
