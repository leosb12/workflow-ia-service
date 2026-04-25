from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class GuideRole(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class GuideScreen(str, Enum):
    POLICY_DESIGNER = "POLICY_DESIGNER"
    POLICY_LIST = "POLICY_LIST"
    ADMIN_USERS = "ADMIN_USERS"
    ADMIN_ROLES = "ADMIN_ROLES"
    ADMIN_DEPARTMENTS = "ADMIN_DEPARTMENTS"
    ADMIN_ANALYTICS = "ADMIN_ANALYTICS"
    ADMIN_AI_SERVICES = "ADMIN_AI_SERVICES"
    ADMIN_SIMULATIONS = "ADMIN_SIMULATIONS"
    EMPLOYEE_DASHBOARD = "EMPLOYEE_DASHBOARD"
    TASK_DETAIL = "TASK_DETAIL"
    TASK_FORM = "TASK_FORM"
    TASK_HISTORY = "TASK_HISTORY"
    GENERAL_ADMIN = "GENERAL_ADMIN"


class GuideDetectedIssueContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    message: str


class GuideContextFormField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    type: str
    required: bool | None = None


class SelectedNodeContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    type: str | None = None
    name: str | None = None
    department: str | None = None
    responsible: str | None = None
    responsible_type: str | None = Field(default=None, alias="responsibleType")
    form_fields: list[GuideContextFormField] = Field(default_factory=list, alias="formFields")
    incoming_nodes: list[str] = Field(default_factory=list, alias="incomingNodes")
    outgoing_nodes: list[str] = Field(default_factory=list, alias="outgoingNodes")


class PolicySummaryContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    has_start_node: bool = Field(default=False, alias="hasStartNode")
    has_end_node: bool = Field(default=False, alias="hasEndNode")
    total_activities: int = Field(default=0, alias="totalActivities")
    total_decisions: int = Field(default=0, alias="totalDecisions")
    activities_without_responsible: int = Field(default=0, alias="activitiesWithoutResponsible")
    activities_without_form: int = Field(default=0, alias="activitiesWithoutForm")
    invalid_connections: int = Field(default=0, alias="invalidConnections")
    decisions_without_routes: int = Field(default=0, alias="decisionsWithoutRoutes")
    parallel_nodes_incomplete: int = Field(default=0, alias="parallelNodesIncomplete")
    orphan_nodes: int = Field(default=0, alias="orphanNodes")


class AdminGuideContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    policy_status: str | None = Field(default=None, alias="policyStatus")
    selected_node: SelectedNodeContext | None = Field(default=None, alias="selectedNode")
    policy_summary: PolicySummaryContext | None = Field(default=None, alias="policySummary")
    detected_issues: list[GuideDetectedIssueContext] = Field(default_factory=list, alias="detectedIssues")
    available_actions: list[str] = Field(default_factory=list, alias="availableActions")
    policy_departments: list[str] = Field(default_factory=list, alias="policyDepartments")


class AdminGuideRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    user_name: str | None = Field(default=None, alias="userName")
    role: GuideRole = GuideRole.ADMIN
    screen: GuideScreen
    question: str
    context: AdminGuideContext = Field(default_factory=AdminGuideContext)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = " ".join((value or "").split())
        if not normalized:
            raise ValueError("question no puede estar vacia")
        return normalized[:500]


class EmployeeCurrentNodeContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    type: str | None = None
    name: str | None = None
    description: str | None = None
    department: str | None = None
    estimated_time: str | None = Field(default=None, alias="estimatedTime")


class EmployeeFormFieldContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    label: str
    type: str
    required: bool = True
    value: str | bool | int | float | dict | list | None = None


class EmployeeFormContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fields: list[EmployeeFormFieldContext] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list, alias="missingRequiredFields")


class EmployeeHistorySummaryContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    completed_steps: int = Field(default=0, alias="completedSteps")
    current_step: str | None = Field(default=None, alias="currentStep")
    pending_steps: int = Field(default=0, alias="pendingSteps")
    last_completed_by: str | None = Field(default=None, alias="lastCompletedBy")


class EmployeeNextPossibleStepContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    condition: str | None = None
    next_node: str | None = Field(default=None, alias="nextNode")
    next_department: str | None = Field(default=None, alias="nextDepartment")


class EmployeeDashboardSummaryContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pending_tasks: int = Field(default=0, alias="pendingTasks")
    in_progress_tasks: int = Field(default=0, alias="inProgressTasks")
    completed_tasks: int = Field(default=0, alias="completedTasks")
    overdue_tasks: int = Field(default=0, alias="overdueTasks")


class EmployeeTaskQueueItemContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str | None = Field(default=None, alias="taskId")
    task_name: str | None = Field(default=None, alias="taskName")
    task_status: str | None = Field(default=None, alias="taskStatus")
    priority: str | None = None
    age_hours: int | None = Field(default=None, alias="ageHours")
    overdue: bool = False
    policy_name: str | None = Field(default=None, alias="policyName")


class EmployeeGuideContext(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str | None = Field(default=None, alias="taskId")
    instance_id: str | None = Field(default=None, alias="instanceId")
    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    current_node: EmployeeCurrentNodeContext | None = Field(default=None, alias="currentNode")
    task_status: str | None = Field(default=None, alias="taskStatus")
    priority: str | None = None
    form: EmployeeFormContext | None = None
    history_summary: EmployeeHistorySummaryContext | None = Field(default=None, alias="historySummary")
    next_possible_steps: list[EmployeeNextPossibleStepContext] = Field(
        default_factory=list,
        alias="nextPossibleSteps",
    )
    dashboard_summary: EmployeeDashboardSummaryContext | None = Field(
        default=None,
        alias="dashboardSummary",
    )
    task_queue: list[EmployeeTaskQueueItemContext] = Field(default_factory=list, alias="taskQueue")
    available_actions: list[str] = Field(default_factory=list, alias="availableActions")


class EmployeeGuideRequest(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    user_name: str | None = Field(default=None, alias="userName")
    role: GuideRole = GuideRole.EMPLOYEE
    screen: GuideScreen
    question: str
    context: EmployeeGuideContext = Field(default_factory=EmployeeGuideContext)

    @field_validator("question")
    @classmethod
    def validate_employee_question(cls, value: str) -> str:
        normalized = " ".join((value or "").split())
        if not normalized:
            raise ValueError("question no puede estar vacia")
        return normalized[:500]
