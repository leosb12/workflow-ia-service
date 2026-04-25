from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class AdminGuideIntent(str, Enum):
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


class GuideSeverity(str, Enum):
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    SUCCESS = "SUCCESS"


class SuggestedResponsible(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    name: str
    reason: str


class SuggestedFormField(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    label: str
    type: str
    required: bool = False


class GuideIssue(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    type: str
    message: str


class SuggestedAction(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    action: str
    label: str


class AdminGuideResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    answer: str
    steps: list[str] = Field(default_factory=list)
    suggested_responsible: SuggestedResponsible | None = Field(
        default=None,
        alias="suggestedResponsible",
    )
    suggested_form: list[SuggestedFormField] = Field(default_factory=list, alias="suggestedForm")
    detected_issues: list[GuideIssue] = Field(default_factory=list, alias="detectedIssues")
    suggested_actions: list[SuggestedAction] = Field(default_factory=list, alias="suggestedActions")
    severity: GuideSeverity = GuideSeverity.INFO
    intent: AdminGuideIntent = AdminGuideIntent.GENERAL_ADMIN_HELP
    source: str = "HEURISTIC"
    available: bool = True
