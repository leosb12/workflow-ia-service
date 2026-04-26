from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class IntencionGuiaAdministrador(str, Enum):
    EXPLAIN_SCREEN = "EXPLAIN_SCREEN"
    WHAT_CAN_I_DO_HERE = "WHAT_CAN_I_DO_HERE"
    SUGGEST_RESPONSIBLE = "SUGGEST_RESPONSIBLE"
    SUGGEST_ACTIVITY_FORM = "SUGGEST_ACTIVITY_FORM"
    SUGGEST_DECISION = "SUGGEST_DECISION"
    SUGGEST_NEXT_ACTIVITY = "SUGGEST_NEXT_ACTIVITY"
    VALIDATE_POLICY = "VALIDATE_POLICY"
    EXPLAIN_POLICY_ERROR = "EXPLAIN_POLICY_ERROR"
    GUIDE_STEP_BY_STEP = "GUIDE_STEP_BY_STEP"
    OPTIMIZE_POLICY = "OPTIMIZE_POLICY"
    HELP_CREATE_POLICY = "HELP_CREATE_POLICY"
    HELP_ACTIVATE_POLICY = "HELP_ACTIVATE_POLICY"
    GENERAL_ADMIN_HELP = "GENERAL_ADMIN_HELP"


class IntencionGuiaFuncionario(str, Enum):
    EXPLAIN_SCREEN = "EXPLAIN_SCREEN"
    WHAT_CAN_I_DO_HERE = "WHAT_CAN_I_DO_HERE"
    EXPLAIN_TASK = "EXPLAIN_TASK"
    EXPLAIN_FORM = "EXPLAIN_FORM"
    EXPLAIN_FIELD = "EXPLAIN_FIELD"
    HELP_COMPLETE_FORM = "HELP_COMPLETE_FORM"
    VALIDATE_BEFORE_COMPLETE = "VALIDATE_BEFORE_COMPLETE"
    EXPLAIN_COMPLETION_ERROR = "EXPLAIN_COMPLETION_ERROR"
    EXPLAIN_NEXT_STEP = "EXPLAIN_NEXT_STEP"
    PRIORITIZE_TASKS = "PRIORITIZE_TASKS"
    EXPLAIN_TASK_STATUS = "EXPLAIN_TASK_STATUS"
    EXPLAIN_WORKFLOW_PROGRESS = "EXPLAIN_WORKFLOW_PROGRESS"
    GUIDE_STEP_BY_STEP = "GUIDE_STEP_BY_STEP"
    GENERAL_EMPLOYEE_HELP = "GENERAL_EMPLOYEE_HELP"


class IntencionGuiaUsuarioMovil(str, Enum):
    EXPLICAR_PANTALLA = "EXPLICAR_PANTALLA"
    QUE_PUEDO_HACER_AQUI = "QUE_PUEDO_HACER_AQUI"
    EXPLICAR_ESTADO_TRAMITE = "EXPLICAR_ESTADO_TRAMITE"
    EXPLICAR_PROGRESO_TRAMITE = "EXPLICAR_PROGRESO_TRAMITE"
    EXPLICAR_ETAPA_ACTUAL = "EXPLICAR_ETAPA_ACTUAL"
    EXPLICAR_HISTORIAL = "EXPLICAR_HISTORIAL"
    EXPLICAR_DOCUMENTOS_FALTANTES = "EXPLICAR_DOCUMENTOS_FALTANTES"
    EXPLICAR_OBSERVACIONES = "EXPLICAR_OBSERVACIONES"
    EXPLICAR_RECHAZO = "EXPLICAR_RECHAZO"
    EXPLICAR_PROXIMO_PASO = "EXPLICAR_PROXIMO_PASO"
    AYUDA_INICIAR_TRAMITE = "AYUDA_INICIAR_TRAMITE"
    AYUDA_SUBIR_DOCUMENTO = "AYUDA_SUBIR_DOCUMENTO"
    GUIA_PASO_A_PASO = "GUIA_PASO_A_PASO"
    AYUDA_GENERAL_USUARIO_MOVIL = "AYUDA_GENERAL_USUARIO_MOVIL"


class SeveridadGuia(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class ResponsableSugerido(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    reason: str


class CampoFormularioSugerido(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    type: str
    required: bool = False


class ProblemaGuia(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    message: str


class AccionSugerida(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    action: str
    label: str


class RespuestaGuiaAdministrador(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    steps: list[str] = Field(default_factory=list)
    suggested_responsible: ResponsableSugerido | None = Field(
        default=None,
        alias="suggestedResponsible",
    )
    suggested_form: list[CampoFormularioSugerido] = Field(default_factory=list, alias="suggestedForm")
    detected_issues: list[ProblemaGuia] = Field(default_factory=list, alias="detectedIssues")
    suggested_actions: list[AccionSugerida] = Field(default_factory=list, alias="suggestedActions")
    severity: SeveridadGuia = SeveridadGuia.INFO
    intent: IntencionGuiaAdministrador = IntencionGuiaAdministrador.GENERAL_ADMIN_HELP
    source: str = "HEURISTIC"
    available: bool = True


class AyudaFormularioFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: str
    help: str


class CampoFaltanteFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    field: str
    message: str


class SugerenciaPrioridadFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    recommended_task_id: str | None = Field(default=None, alias="recommendedTaskId")
    reason: str


class RespuestaGuiaFuncionario(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    steps: list[str] = Field(default_factory=list)
    form_help: list[AyudaFormularioFuncionario] = Field(default_factory=list, alias="formHelp")
    missing_fields: list[CampoFaltanteFuncionario] = Field(default_factory=list, alias="missingFields")
    priority_suggestion: SugerenciaPrioridadFuncionario | None = Field(
        default=None,
        alias="prioritySuggestion",
    )
    next_step_explanation: str | None = Field(default=None, alias="nextStepExplanation")
    suggested_actions: list[AccionSugerida] = Field(default_factory=list, alias="suggestedActions")
    severity: SeveridadGuia = SeveridadGuia.INFO
    intent: IntencionGuiaFuncionario = IntencionGuiaFuncionario.GENERAL_EMPLOYEE_HELP
    source: str = "HEURISTIC"
    available: bool = True


AdminGuideIntent = IntencionGuiaAdministrador
EmployeeGuideIntent = IntencionGuiaFuncionario
GuideSeverity = SeveridadGuia
SuggestedResponsible = ResponsableSugerido
SuggestedFormField = CampoFormularioSugerido
GuideIssue = ProblemaGuia
SuggestedAction = AccionSugerida
AdminGuideResponse = RespuestaGuiaAdministrador
EmployeeFormHelp = AyudaFormularioFuncionario
EmployeeMissingField = CampoFaltanteFuncionario
EmployeePrioritySuggestion = SugerenciaPrioridadFuncionario
EmployeeGuideResponse = RespuestaGuiaFuncionario


class RespuestaGuiaUsuarioMovil(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    respuesta: str = Field(alias="answer")
    pasos: list[str] = Field(default_factory=list, alias="steps")
    estado_explicado: str | None = Field(default=None, alias="estadoExplicado")
    progreso_explicado: str | None = Field(default=None, alias="progresoExplicado")
    documentos_faltantes: list[str] = Field(default_factory=list, alias="documentosFaltantes")
    proximos_pasos: list[str] = Field(default_factory=list, alias="proximosPasos")
    acciones_sugeridas: list[AccionSugerida] = Field(default_factory=list, alias="accionesSugeridas")
    severidad: SeveridadGuia = Field(default=SeveridadGuia.INFO, alias="severity")
    intencion: IntencionGuiaUsuarioMovil = Field(
        default=IntencionGuiaUsuarioMovil.AYUDA_GENERAL_USUARIO_MOVIL,
        alias="intent",
    )
    fuente: str = Field(default="HEURISTIC", alias="source")
    disponible: bool = Field(default=True, alias="available")


MobileUserGuideIntent = IntencionGuiaUsuarioMovil
MobileUserGuideResponse = RespuestaGuiaUsuarioMovil
