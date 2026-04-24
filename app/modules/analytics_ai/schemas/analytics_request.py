from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class _FlexibleModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PolicyAverageMetric(_FlexibleModel):
    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    average_hours: float | None = Field(default=None, alias="averageHours")
    completed_instances: int | None = Field(default=None, alias="completedInstances")


class NodeAverageMetric(_FlexibleModel):
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(default=None, alias="nodeName")
    average_hours: float | None = Field(default=None, alias="averageHours")
    completed_tasks: int | None = Field(default=None, alias="completedTasks")


class DepartmentAverageMetric(_FlexibleModel):
    department_id: str | None = Field(default=None, alias="departmentId")
    department_name: str | None = Field(default=None, alias="departmentName")
    average_hours: float | None = Field(default=None, alias="averageHours")
    completed_tasks: int | None = Field(default=None, alias="completedTasks")


class OfficialAverageMetric(_FlexibleModel):
    official_id: str | None = Field(default=None, alias="officialId")
    official_name: str | None = Field(default=None, alias="officialName")
    average_hours: float | None = Field(default=None, alias="averageHours")
    completed_tasks: int | None = Field(default=None, alias="completedTasks")


class ActivitySummaryMetric(_FlexibleModel):
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(default=None, alias="nodeName")
    average_hours: float | None = Field(default=None, alias="averageHours")


class PendingByOfficialMetric(_FlexibleModel):
    official_id: str | None = Field(default=None, alias="officialId")
    official_name: str | None = Field(default=None, alias="officialName")
    pending_tasks: int | None = Field(default=None, alias="pendingTasks")
    oldest_task_age_hours: float | None = Field(default=None, alias="oldestTaskAgeHours")


class PendingByDepartmentMetric(_FlexibleModel):
    department_id: str | None = Field(default=None, alias="departmentId")
    department_name: str | None = Field(default=None, alias="departmentName")
    pending_tasks: int | None = Field(default=None, alias="pendingTasks")
    oldest_task_age_hours: float | None = Field(default=None, alias="oldestTaskAgeHours")


class PendingByPolicyMetric(_FlexibleModel):
    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    pending_tasks: int | None = Field(default=None, alias="pendingTasks")
    oldest_task_age_hours: float | None = Field(default=None, alias="oldestTaskAgeHours")


class PendingByNodeMetric(_FlexibleModel):
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(default=None, alias="nodeName")
    pending_tasks: int | None = Field(default=None, alias="pendingTasks")
    oldest_task_age_hours: float | None = Field(default=None, alias="oldestTaskAgeHours")


class OldestPendingTaskMetric(_FlexibleModel):
    task_id: str | None = Field(default=None, alias="taskId")
    policy_name: str | None = Field(default=None, alias="policyName")
    node_name: str | None = Field(default=None, alias="nodeName")
    assigned_to_name: str | None = Field(default=None, alias="assignedToName")
    department_name: str | None = Field(default=None, alias="departmentName")
    age_hours: float | None = Field(default=None, alias="ageHours")
    created_at: str | None = Field(default=None, alias="createdAt")


class GeneralMetrics(BaseModel):
    total_policies: int | None = Field(default=None, alias="totalPolicies")
    active_policies: int | None = Field(default=None, alias="activePolicies")
    total_instances: int | None = Field(default=None, alias="totalInstances")
    in_progress_instances: int | None = Field(default=None, alias="inProgressInstances")
    completed_instances: int | None = Field(default=None, alias="completedInstances")
    rejected_instances: int | None = Field(default=None, alias="rejectedInstances")
    pending_tasks: int | None = Field(default=None, alias="pendingTasks")
    completed_tasks: int | None = Field(default=None, alias="completedTasks")
    average_resolution_time_hours: float | None = Field(default=None, alias="averageResolutionTimeHours")
    has_enough_resolution_time_data: bool | None = Field(default=None, alias="hasEnoughResolutionTimeData")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class AttentionTimes(BaseModel):
    average_by_policy: list[PolicyAverageMetric] = Field(default_factory=list, alias="averageByPolicy")
    average_by_node: list[NodeAverageMetric] = Field(default_factory=list, alias="averageByNode")
    average_by_department: list[DepartmentAverageMetric] = Field(default_factory=list, alias="averageByDepartment")
    average_by_official: list[OfficialAverageMetric] = Field(default_factory=list, alias="averageByOfficial")
    slowest_activity: ActivitySummaryMetric | None = Field(default=None, alias="slowestActivity")
    fastest_activity: ActivitySummaryMetric | None = Field(default=None, alias="fastestActivity")
    has_enough_data: bool | None = Field(default=None, alias="hasEnoughData")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class TaskAccumulation(BaseModel):
    pending_by_official: list[PendingByOfficialMetric] = Field(default_factory=list, alias="pendingByOfficial")
    pending_by_department: list[PendingByDepartmentMetric] = Field(default_factory=list, alias="pendingByDepartment")
    pending_by_policy: list[PendingByPolicyMetric] = Field(default_factory=list, alias="pendingByPolicy")
    pending_by_node: list[PendingByNodeMetric] = Field(default_factory=list, alias="pendingByNode")
    oldest_pending_tasks: list[OldestPendingTaskMetric] = Field(default_factory=list, alias="oldestPendingTasks")

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class DashboardAnalyticsRequest(BaseModel):
    general: GeneralMetrics = Field(default_factory=GeneralMetrics)
    attention_times: AttentionTimes = Field(default_factory=AttentionTimes, alias="attentionTimes")
    task_accumulation: TaskAccumulation = Field(default_factory=TaskAccumulation, alias="taskAccumulation")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
    )


class WorkflowNode(_FlexibleModel):
    id: str | None = None
    name: str | None = None
    type: str | None = None
    description: str | None = None


class WorkflowTransition(_FlexibleModel):
    id: str | None = None
    from_node: str | None = Field(default=None, alias="from")
    to_node: str | None = Field(default=None, alias="to")
    label: str | None = None
    condition: str | None = None


class WorkflowStructure(BaseModel):
    nodes: list[WorkflowNode] = Field(default_factory=list)
    transitions: list[WorkflowTransition] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class PolicyImprovementRequest(BaseModel):
    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    workflow_structure: WorkflowStructure | None = Field(default=None, alias="workflowStructure")
    dashboard: DashboardAnalyticsRequest
    context: dict[str, Any] | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
