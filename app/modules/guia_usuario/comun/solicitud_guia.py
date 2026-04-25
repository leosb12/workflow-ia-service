from enum import Enum

from pydantic import BaseModel, ConfigDict, Field, field_validator


class RolGuia(str, Enum):
    ADMIN = "ADMIN"
    EMPLOYEE = "EMPLOYEE"


class PantallaGuia(str, Enum):
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


class ContextoProblemaDetectadoGuia(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    message: str


class CampoFormularioContextoGuia(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    type: str
    required: bool | None = None


class ContextoNodoSeleccionado(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    type: str | None = None
    name: str | None = None
    department: str | None = None
    responsible: str | None = None
    responsible_type: str | None = Field(default=None, alias="responsibleType")
    form_fields: list[CampoFormularioContextoGuia] = Field(default_factory=list, alias="formFields")
    incoming_nodes: list[str] = Field(default_factory=list, alias="incomingNodes")
    outgoing_nodes: list[str] = Field(default_factory=list, alias="outgoingNodes")


class ContextoResumenPolitica(BaseModel):
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


class ContextoGuiaAdministrador(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    policy_status: str | None = Field(default=None, alias="policyStatus")
    selected_node: ContextoNodoSeleccionado | None = Field(default=None, alias="selectedNode")
    policy_summary: ContextoResumenPolitica | None = Field(default=None, alias="policySummary")
    detected_issues: list[ContextoProblemaDetectadoGuia] = Field(default_factory=list, alias="detectedIssues")
    available_actions: list[str] = Field(default_factory=list, alias="availableActions")
    policy_departments: list[str] = Field(default_factory=list, alias="policyDepartments")


class SolicitudGuiaAdministrador(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    user_name: str | None = Field(default=None, alias="userName")
    role: RolGuia = RolGuia.ADMIN
    screen: PantallaGuia
    question: str
    context: ContextoGuiaAdministrador = Field(default_factory=ContextoGuiaAdministrador)

    @field_validator("question")
    @classmethod
    def validate_question(cls, value: str) -> str:
        normalized = " ".join((value or "").split())
        if not normalized:
            raise ValueError("question no puede estar vacia")
        return normalized[:500]


class ContextoNodoActualFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    type: str | None = None
    name: str | None = None
    description: str | None = None
    department: str | None = None
    estimated_time: str | None = Field(default=None, alias="estimatedTime")


class ContextoCampoFormularioFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    label: str
    type: str
    required: bool = True
    value: str | bool | int | float | dict | list | None = None


class ContextoFormularioFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    fields: list[ContextoCampoFormularioFuncionario] = Field(default_factory=list)
    missing_required_fields: list[str] = Field(default_factory=list, alias="missingRequiredFields")


class ContextoResumenHistorialFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    completed_steps: int = Field(default=0, alias="completedSteps")
    current_step: str | None = Field(default=None, alias="currentStep")
    pending_steps: int = Field(default=0, alias="pendingSteps")
    last_completed_by: str | None = Field(default=None, alias="lastCompletedBy")


class ContextoSiguientePasoPosibleFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    condition: str | None = None
    next_node: str | None = Field(default=None, alias="nextNode")
    next_department: str | None = Field(default=None, alias="nextDepartment")


class ContextoResumenPanelFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    pending_tasks: int = Field(default=0, alias="pendingTasks")
    in_progress_tasks: int = Field(default=0, alias="inProgressTasks")
    completed_tasks: int = Field(default=0, alias="completedTasks")
    overdue_tasks: int = Field(default=0, alias="overdueTasks")


class ContextoElementoColaTareaFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str | None = Field(default=None, alias="taskId")
    task_name: str | None = Field(default=None, alias="taskName")
    task_status: str | None = Field(default=None, alias="taskStatus")
    priority: str | None = None
    age_hours: int | None = Field(default=None, alias="ageHours")
    overdue: bool = False
    policy_name: str | None = Field(default=None, alias="policyName")


class ContextoGuiaFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    task_id: str | None = Field(default=None, alias="taskId")
    instance_id: str | None = Field(default=None, alias="instanceId")
    policy_id: str | None = Field(default=None, alias="policyId")
    policy_name: str | None = Field(default=None, alias="policyName")
    current_node: ContextoNodoActualFuncionario | None = Field(default=None, alias="currentNode")
    task_status: str | None = Field(default=None, alias="taskStatus")
    priority: str | None = None
    form: ContextoFormularioFuncionario | None = None
    history_summary: ContextoResumenHistorialFuncionario | None = Field(default=None, alias="historySummary")
    next_possible_steps: list[ContextoSiguientePasoPosibleFuncionario] = Field(
        default_factory=list,
        alias="nextPossibleSteps",
    )
    dashboard_summary: ContextoResumenPanelFuncionario | None = Field(
        default=None,
        alias="dashboardSummary",
    )
    task_queue: list[ContextoElementoColaTareaFuncionario] = Field(default_factory=list, alias="taskQueue")
    available_actions: list[str] = Field(default_factory=list, alias="availableActions")


class SolicitudGuiaFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    user_id: str = Field(alias="userId")
    user_name: str | None = Field(default=None, alias="userName")
    role: RolGuia = RolGuia.EMPLOYEE
    screen: PantallaGuia
    question: str
    context: ContextoGuiaFuncionario = Field(default_factory=ContextoGuiaFuncionario)

    @field_validator("question")
    @classmethod
    def validate_employee_question(cls, value: str) -> str:
        normalized = " ".join((value or "").split())
        if not normalized:
            raise ValueError("question no puede estar vacia")
        return normalized[:500]


GuideRole = RolGuia
GuideScreen = PantallaGuia
GuideDetectedIssueContext = ContextoProblemaDetectadoGuia
GuideContextFormField = CampoFormularioContextoGuia
SelectedNodeContext = ContextoNodoSeleccionado
PolicySummaryContext = ContextoResumenPolitica
AdminGuideContext = ContextoGuiaAdministrador
AdminGuideRequest = SolicitudGuiaAdministrador
EmployeeCurrentNodeContext = ContextoNodoActualFuncionario
EmployeeFormFieldContext = ContextoCampoFormularioFuncionario
EmployeeFormContext = ContextoFormularioFuncionario
EmployeeHistorySummaryContext = ContextoResumenHistorialFuncionario
EmployeeNextPossibleStepContext = ContextoSiguientePasoPosibleFuncionario
EmployeeDashboardSummaryContext = ContextoResumenPanelFuncionario
EmployeeTaskQueueItemContext = ContextoElementoColaTareaFuncionario
EmployeeGuideContext = ContextoGuiaFuncionario
EmployeeGuideRequest = SolicitudGuiaFuncionario
