import logging
from typing import Any

from pydantic import ValidationError

from app.modules.analitica.prompts.prompts_analitica import PromptsAnalitica
from app.modules.analitica.modelos.solicitud_analitica import (
    DashboardAnalyticsRequest,
    PendingByOfficialMetric,
    PolicyImprovementRequest,
)
from app.modules.analitica.modelos.respuesta_analitica import (
    BottleneckAnalysisResponse,
    BottleneckItem,
    IntelligentSummaryResponse,
    PolicyImprovementResponse,
    PolicyIssueItem,
    TaskRedistributionItem,
    TaskRedistributionResponse,
)
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)

_PRIORITY_ORDER = {"HIGH": 0, "MEDIUM": 1, "LOW": 2}


class ServicioAnalitica:
    def __init__(
        self,
        prompt_runner: PromptRunner,
        json_parser: JsonObjectParser,
        prompts: PromptsAnalitica,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.json_parser = json_parser
        self.prompts = prompts

    async def analyze_bottlenecks(
        self,
        request: DashboardAnalyticsRequest,
    ) -> BottleneckAnalysisResponse:
        if self._has_insufficient_bottleneck_data(request):
            return self._insufficient_bottlenecks_response()

        return await self._run_with_fallback(
            system_prompt=self.prompts.build_bottlenecks_system_prompt(),
            user_prompt=self.prompts.build_bottlenecks_user_prompt(request),
            sanitizer=lambda payload: self._sanitize_bottlenecks(payload, request),
            fallback_factory=self._unavailable_bottlenecks_response,
            log_message="No se pudo completar el analisis de cuellos de botella",
        )

    async def recommend_task_redistribution(
        self,
        request: DashboardAnalyticsRequest,
    ) -> TaskRedistributionResponse:
        if self._has_insufficient_redistribution_data(request):
            return self._insufficient_redistribution_response()

        if not self._exists_lower_load_receiver(request):
            return TaskRedistributionResponse(
                summary=(
                    "No se recomienda redistribucion porque no existe un funcionario receptor con menor carga "
                    "segun los datos recibidos."
                ),
                recommendations=[],
                source="AI",
                available=True,
            )

        return await self._run_with_fallback(
            system_prompt=self.prompts.build_task_redistribution_system_prompt(),
            user_prompt=self.prompts.build_task_redistribution_user_prompt(request),
            sanitizer=lambda payload: self._sanitize_task_redistribution(payload, request),
            fallback_factory=self._unavailable_task_redistribution_response,
            log_message="No se pudo completar el analisis de redistribucion de tareas",
        )

    async def improve_policy(
        self,
        request: PolicyImprovementRequest,
    ) -> PolicyImprovementResponse:
        if self._has_insufficient_policy_data(request):
            return self._insufficient_policy_improvement_response()

        return await self._run_with_fallback(
            system_prompt=self.prompts.build_policy_improvement_system_prompt(),
            user_prompt=self.prompts.build_policy_improvement_user_prompt(request),
            sanitizer=lambda payload: self._sanitize_policy_improvement(payload, request),
            fallback_factory=self._unavailable_policy_improvement_response,
            log_message="No se pudo completar el analisis de mejora de politica",
        )

    async def build_intelligent_summary(
        self,
        request: DashboardAnalyticsRequest,
    ) -> IntelligentSummaryResponse:
        return IntelligentSummaryResponse(
            bottlenecks=await self.analyze_bottlenecks(request),
            taskRedistribution=await self.recommend_task_redistribution(request),
            policyImprovement=await self.improve_policy(PolicyImprovementRequest(dashboard=request)),
        )

    async def _run_with_fallback(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        sanitizer,
        fallback_factory,
        log_message: str,
    ):
        try:
            raw_json = await self.prompt_runner.run_json_prompt(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
            )
            payload = self.json_parser.parse(raw_json)
            return sanitizer(payload)
        except Exception as exc:
            log.warning("%s: %s", log_message, exc)
            return fallback_factory()

    def _sanitize_bottlenecks(
        self,
        payload: dict[str, Any],
        request: DashboardAnalyticsRequest,
    ) -> BottleneckAnalysisResponse:
        allowed_names = self._allowed_bottleneck_names(request)
        items: list[BottleneckItem] = []

        for raw_item in self._as_list(payload.get("bottlenecks")):
            if not isinstance(raw_item, dict):
                continue
            item_type = self._normalize_level(raw_item.get("type"), allowed_names.keys())
            name = self._clean_text(raw_item.get("name"))
            if item_type is None or not name or name not in allowed_names.get(item_type, set()):
                continue
            items.append(
                BottleneckItem(
                    type=item_type,
                    name=name,
                    severity=self._normalize_level(raw_item.get("severity"), {"LOW", "MEDIUM", "HIGH"}) or "LOW",
                    evidence=self._clean_text(raw_item.get("evidence"))
                    or "La evidencia devuelta por la IA no fue suficiente para detallar este hallazgo.",
                    impact=self._clean_text(raw_item.get("impact"))
                    or "Puede afectar la continuidad operativa del flujo.",
                    recommendation=self._clean_text(raw_item.get("recommendation"))
                    or "Revisar la carga asociada a este punto del proceso.",
                )
            )

        items = self._sort_and_limit(items, "severity")
        summary = self._clean_text(payload.get("summary"))
        if not summary:
            summary = (
                "No hay datos suficientes para detectar cuellos de botella con evidencia."
                if not items
                else f"Se detectaron {len(items)} cuellos de botella con evidencia en las metricas recibidas."
            )

        try:
            return BottleneckAnalysisResponse(
                summary=summary,
                bottlenecks=items,
                source="AI",
                available=True,
            )
        except ValidationError:
            return self._unavailable_bottlenecks_response()

    def _sanitize_task_redistribution(
        self,
        payload: dict[str, Any],
        request: DashboardAnalyticsRequest,
    ) -> TaskRedistributionResponse:
        allowed_officials = self._allowed_official_names(request)
        pending_map = self._pending_by_official_map(request)
        items: list[TaskRedistributionItem] = []

        for raw_item in self._as_list(payload.get("recommendations")):
            if not isinstance(raw_item, dict):
                continue
            from_official = self._clean_text(raw_item.get("fromOfficial"))
            to_official = self._clean_text(raw_item.get("toOfficial"))
            if (
                not from_official
                or not to_official
                or from_official == to_official
                or from_official not in allowed_officials
                or to_official not in allowed_officials
            ):
                continue
            from_pending = pending_map.get(from_official)
            to_pending = pending_map.get(to_official)
            if from_pending is None or to_pending is None or to_pending >= from_pending:
                continue
            items.append(
                TaskRedistributionItem(
                    fromOfficial=from_official,
                    toOfficial=to_official,
                    reason=self._clean_text(raw_item.get("reason"))
                    or "Tiene mayor carga pendiente y antiguedad superior respecto al receptor propuesto.",
                    priority=self._normalize_level(raw_item.get("priority"), {"LOW", "MEDIUM", "HIGH"}) or "LOW",
                    expectedImpact=self._clean_text(raw_item.get("expectedImpact"))
                    or "Reducir la acumulacion y mejorar los tiempos de atencion.",
                )
            )

        items = self._sort_and_limit(items, "priority")
        summary = self._clean_text(payload.get("summary"))
        if not summary:
            summary = (
                "No hay datos suficientes para recomendar redistribucion de tareas."
                if not items
                else f"Se generaron {len(items)} recomendaciones de redistribucion con evidencia en los datos."
            )

        try:
            return TaskRedistributionResponse(
                summary=summary,
                recommendations=items,
                source="AI",
                available=True,
            )
        except ValidationError:
            return self._unavailable_task_redistribution_response()

    def _sanitize_policy_improvement(
        self,
        payload: dict[str, Any],
        request: PolicyImprovementRequest,
    ) -> PolicyImprovementResponse:
        allowed_steps = self._allowed_policy_steps(request)
        items: list[PolicyIssueItem] = []

        for raw_item in self._as_list(payload.get("policyIssues")):
            if not isinstance(raw_item, dict):
                continue
            node_or_step = self._clean_text(raw_item.get("nodeOrStep"))
            if not node_or_step or node_or_step not in allowed_steps:
                continue
            items.append(
                PolicyIssueItem(
                    nodeOrStep=node_or_step,
                    problem=self._clean_text(raw_item.get("problem"))
                    or "Se identifico una oportunidad de mejora en este punto del flujo.",
                    evidence=self._clean_text(raw_item.get("evidence"))
                    or "Las metricas disponibles muestran un comportamiento que amerita revision.",
                    recommendation=self._clean_text(raw_item.get("recommendation"))
                    or "Revisar este paso con base en las metricas reales recibidas.",
                    priority=self._normalize_level(raw_item.get("priority"), {"LOW", "MEDIUM", "HIGH"}) or "LOW",
                )
            )

        items = self._sort_and_limit(items, "priority")
        summary = self._clean_text(payload.get("summary"))
        if not summary:
            summary = (
                "No hay datos suficientes para recomendar mejoras de politica con evidencia."
                if not items
                else f"Se detectaron {len(items)} oportunidades de mejora sobre la politica o flujo analizado."
            )

        try:
            return PolicyImprovementResponse(
                summary=summary,
                policyIssues=items,
                source="AI",
                available=True,
            )
        except ValidationError:
            return self._unavailable_policy_improvement_response()

    def _allowed_bottleneck_names(self, request: DashboardAnalyticsRequest) -> dict[str, set[str]]:
        return {
            "NODE": {
                *self._collect_values(request.attention_times.average_by_node, "node_name"),
                *self._collect_values(request.task_accumulation.pending_by_node, "node_name"),
                *self._collect_optional_value(request.attention_times.slowest_activity, "node_name"),
                *self._collect_optional_value(request.attention_times.fastest_activity, "node_name"),
            },
            "DEPARTMENT": {
                *self._collect_values(request.attention_times.average_by_department, "department_name"),
                *self._collect_values(request.task_accumulation.pending_by_department, "department_name"),
            },
            "OFFICIAL": {
                *self._collect_values(request.attention_times.average_by_official, "official_name"),
                *self._collect_values(request.task_accumulation.pending_by_official, "official_name"),
            },
            "POLICY": {
                *self._collect_values(request.attention_times.average_by_policy, "policy_name"),
                *self._collect_values(request.task_accumulation.pending_by_policy, "policy_name"),
            },
            "TASK": {
                *self._collect_values(request.task_accumulation.oldest_pending_tasks, "task_id"),
            },
        }

    def _allowed_official_names(self, request: DashboardAnalyticsRequest) -> set[str]:
        return {
            *self._collect_values(request.attention_times.average_by_official, "official_name"),
            *self._collect_values(request.task_accumulation.pending_by_official, "official_name"),
        }

    def _allowed_policy_steps(self, request: PolicyImprovementRequest) -> set[str]:
        allowed_steps = {
            *self._collect_values(request.dashboard.attention_times.average_by_node, "node_name"),
            *self._collect_values(request.dashboard.task_accumulation.pending_by_node, "node_name"),
            *self._collect_values(request.dashboard.attention_times.average_by_policy, "policy_name"),
            *self._collect_values(request.dashboard.task_accumulation.pending_by_policy, "policy_name"),
            *self._collect_optional_value(request.dashboard.attention_times.slowest_activity, "node_name"),
            *self._collect_optional_value(request.dashboard.attention_times.fastest_activity, "node_name"),
        }
        if request.policy_name:
            allowed_steps.add(request.policy_name.strip())
        if request.workflow_structure:
            allowed_steps.update(self._collect_values(request.workflow_structure.nodes, "name"))
            allowed_steps.update(self._collect_values(request.workflow_structure.nodes, "id"))
            allowed_steps.update(self._collect_values(request.workflow_structure.transitions, "label"))
            allowed_steps.update(self._collect_values(request.workflow_structure.transitions, "id"))
        return {value for value in allowed_steps if value}

    def _pending_by_official_map(self, request: DashboardAnalyticsRequest) -> dict[str, int]:
        mapping: dict[str, int] = {}
        for item in request.task_accumulation.pending_by_official:
            if item.official_name and item.pending_tasks is not None:
                mapping[item.official_name] = item.pending_tasks
        return mapping

    def _has_insufficient_bottleneck_data(self, request: DashboardAnalyticsRequest) -> bool:
        return (
            not request.attention_times.has_enough_data
            and not request.general.has_enough_resolution_time_data
            and not any(
                [
                    request.attention_times.average_by_node,
                    request.attention_times.average_by_department,
                    request.attention_times.average_by_official,
                    request.attention_times.average_by_policy,
                    request.task_accumulation.pending_by_node,
                    request.task_accumulation.pending_by_department,
                    request.task_accumulation.pending_by_official,
                    request.task_accumulation.pending_by_policy,
                    request.task_accumulation.oldest_pending_tasks,
                ]
            )
        )

    def _has_insufficient_redistribution_data(self, request: DashboardAnalyticsRequest) -> bool:
        return len(self._valid_pending_officials(request.task_accumulation.pending_by_official)) < 2

    def _has_insufficient_policy_data(self, request: PolicyImprovementRequest) -> bool:
        dashboard = request.dashboard
        has_metrics = any(
            [
                dashboard.attention_times.average_by_node,
                dashboard.task_accumulation.pending_by_node,
                dashboard.attention_times.average_by_policy,
                dashboard.task_accumulation.pending_by_policy,
                dashboard.task_accumulation.oldest_pending_tasks,
            ]
        )
        has_structure = bool(
            request.workflow_structure
            and (request.workflow_structure.nodes or request.workflow_structure.transitions)
        )
        return not has_metrics and not has_structure and not request.policy_name and not request.policy_id

    def _exists_lower_load_receiver(self, request: DashboardAnalyticsRequest) -> bool:
        officials = self._valid_pending_officials(request.task_accumulation.pending_by_official)
        if len(officials) < 2:
            return False
        pending_values = [item.pending_tasks for item in officials if item.pending_tasks is not None]
        return bool(pending_values) and min(pending_values) < max(pending_values)

    def _valid_pending_officials(
        self,
        officials: list[PendingByOfficialMetric],
    ) -> list[PendingByOfficialMetric]:
        return [
            item
            for item in officials
            if item.official_name and item.pending_tasks is not None
        ]

    def _sort_and_limit(self, items: list[Any], field_name: str) -> list[Any]:
        return sorted(
            items,
            key=lambda item: _PRIORITY_ORDER.get(getattr(item, field_name), 99),
        )[:5]

    def _clean_text(self, value: Any) -> str:
        if not isinstance(value, str):
            return ""
        cleaned = " ".join(value.strip().split())
        return cleaned[:500]

    def _normalize_level(self, value: Any, allowed: Any) -> str | None:
        if not isinstance(value, str):
            return None
        normalized = value.strip().upper()
        return normalized if normalized in allowed else None

    def _collect_values(self, items: list[Any], attribute: str) -> set[str]:
        values: set[str] = set()
        for item in items:
            value = getattr(item, attribute, None)
            if isinstance(value, str) and value.strip():
                values.add(value.strip())
        return values

    def _collect_optional_value(self, item: Any, attribute: str) -> set[str]:
        if item is None:
            return set()
        value = getattr(item, attribute, None)
        if isinstance(value, str) and value.strip():
            return {value.strip()}
        return set()

    def _as_list(self, value: Any) -> list[Any]:
        return value if isinstance(value, list) else []

    def _insufficient_bottlenecks_response(self) -> BottleneckAnalysisResponse:
        return BottleneckAnalysisResponse(
            summary="No hay datos suficientes para detectar cuellos de botella con evidencia.",
            bottlenecks=[],
            source="AI",
            available=True,
        )

    def _insufficient_redistribution_response(self) -> TaskRedistributionResponse:
        return TaskRedistributionResponse(
            summary="No hay datos suficientes para recomendar redistribucion de tareas.",
            recommendations=[],
            source="AI",
            available=True,
        )

    def _insufficient_policy_improvement_response(self) -> PolicyImprovementResponse:
        return PolicyImprovementResponse(
            summary="No hay datos suficientes para recomendar mejoras de politica con evidencia.",
            policyIssues=[],
            source="AI",
            available=True,
        )

    def _unavailable_bottlenecks_response(self) -> BottleneckAnalysisResponse:
        return BottleneckAnalysisResponse(
            summary="El analisis inteligente no esta disponible en este momento.",
            bottlenecks=[],
            source="AI",
            available=False,
        )

    def _unavailable_task_redistribution_response(self) -> TaskRedistributionResponse:
        return TaskRedistributionResponse(
            summary="El analisis inteligente no esta disponible en este momento.",
            recommendations=[],
            source="AI",
            available=False,
        )

    def _unavailable_policy_improvement_response(self) -> PolicyImprovementResponse:
        return PolicyImprovementResponse(
            summary="El analisis inteligente no esta disponible en este momento.",
            policyIssues=[],
            source="AI",
            available=False,
        )


AnalyticsAiService = ServicioAnalitica
