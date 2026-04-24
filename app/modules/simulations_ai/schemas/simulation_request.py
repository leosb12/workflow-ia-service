from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class _FlexibleModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SimulationPolicyRef(_FlexibleModel):
    id: str | None = None
    nombre: str | None = Field(
        default=None,
        validation_alias=AliasChoices("nombre", "name"),
        serialization_alias="nombre",
    )


class SimulationConfiguration(_FlexibleModel):
    instances: int | None = None
    base_node_duration_hours: float | None = Field(default=None, alias="baseNodeDurationHours")
    variability_percent: float | None = Field(default=None, alias="variabilityPercent")
    include_ai_analysis: bool | None = Field(default=None, alias="includeAiAnalysis")
    random_seed: int | None = Field(default=None, alias="randomSeed")


class SimulationNodeStat(_FlexibleModel):
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(default=None, alias="nodeName")
    node_type: str | None = Field(default=None, alias="nodeType")
    executions: int | None = None
    total_estimated_time_hours: float | None = Field(default=None, alias="totalEstimatedTimeHours")
    average_estimated_time_hours: float | None = Field(default=None, alias="averageEstimatedTimeHours")
    load_percentage: float | None = Field(default=None, alias="loadPercentage")
    bottleneck: bool | None = None


class SimulationDecisionStat(_FlexibleModel):
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(default=None, alias="nodeName")
    total_decisions: int | None = Field(default=None, alias="totalDecisions")
    outcomes: dict[str, int] = Field(default_factory=dict)


class SimulationResult(_FlexibleModel):
    instances_simulated: int | None = Field(default=None, alias="instancesSimulated")
    total_estimated_time_hours: float | None = Field(default=None, alias="totalEstimatedTimeHours")
    average_estimated_time_hours: float | None = Field(default=None, alias="averageEstimatedTimeHours")
    highest_load_node_id: str | None = Field(default=None, alias="highestLoadNodeId")
    highest_load_node_name: str | None = Field(default=None, alias="highestLoadNodeName")
    highest_load_percentage: float | None = Field(default=None, alias="highestLoadPercentage")
    bottleneck_node_ids: list[str] = Field(default_factory=list, alias="bottleneckNodeIds")
    bottleneck_node_names: list[str] = Field(default_factory=list, alias="bottleneckNodeNames")
    node_stats: list[SimulationNodeStat] = Field(default_factory=list, alias="nodeStats")
    decision_stats: list[SimulationDecisionStat] = Field(default_factory=list, alias="decisionStats")
    warnings: list[str] = Field(default_factory=list)


class SimulationAnalysisRequest(BaseModel):
    policy: SimulationPolicyRef | None = None
    configuration: SimulationConfiguration = Field(default_factory=SimulationConfiguration)
    result: SimulationResult | None = None
    actor_id: str | None = Field(default=None, alias="actorId")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SimulationComparisonStats(_FlexibleModel):
    first_average_estimated_time_hours: float | None = Field(default=None, alias="firstAverageEstimatedTimeHours")
    second_average_estimated_time_hours: float | None = Field(default=None, alias="secondAverageEstimatedTimeHours")
    first_bottleneck_count: int | None = Field(default=None, alias="firstBottleneckCount")
    second_bottleneck_count: int | None = Field(default=None, alias="secondBottleneckCount")
    average_time_difference_hours: float | None = Field(default=None, alias="averageTimeDifferenceHours")
    more_efficient_policy_id: str | None = Field(default=None, alias="moreEfficientPolicyId")
    more_efficient_policy_name: str | None = Field(default=None, alias="moreEfficientPolicyName")
    conclusion: str | None = None


class SimulationComparisonRequest(BaseModel):
    first_policy: SimulationPolicyRef | None = Field(default=None, alias="firstPolicy")
    second_policy: SimulationPolicyRef | None = Field(default=None, alias="secondPolicy")
    configuration: SimulationConfiguration = Field(default_factory=SimulationConfiguration)
    comparison: SimulationComparisonStats | None = None
    actor_id: str | None = Field(default=None, alias="actorId")
    context: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="allow")
