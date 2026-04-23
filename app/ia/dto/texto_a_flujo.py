from typing import Literal
from pydantic import BaseModel, ConfigDict, Field


class TextoAFlujoRequest(BaseModel):
    descripcion: str = Field(min_length=1, max_length=12000)
    context: "GenerationContext | None" = None


class GenerationContextDepartment(BaseModel):
    id: str
    nombre: str

    model_config = ConfigDict(extra="forbid")


class GenerationContext(BaseModel):
    departamentos: list[GenerationContextDepartment] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class Policy(BaseModel):
    name: str
    description: str
    objective: str
    version: str = "1.0"

    model_config = ConfigDict(extra="forbid")


class Role(BaseModel):
    id: str
    name: str
    description: str

    model_config = ConfigDict(extra="forbid")


class WorkflowNode(BaseModel):
    id: str
    type: Literal["start", "task", "decision", "parallel_start", "parallel_end", "end"]
    name: str
    description: str
    responsible_role_id: str | None = Field(default=None, alias="responsibleRoleId")
    form_id: str | None = Field(default=None, alias="formId")
    decision_criteria: str | None = Field(default=None, alias="decisionCriteria")
    responsible_type: Literal["department", "initiator"] | None = Field(
        default=None,
        alias="responsibleType",
    )
    department_hint: str | None = Field(default=None, alias="departmentHint")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class Transition(BaseModel):
    id: str
    from_: str = Field(alias="from")
    to: str
    label: str
    condition: str | None = None

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class FormField(BaseModel):
    id: str
    label: str
    type: Literal[
        "text",
        "textarea",
        "number",
        "date",
        "boolean",
        "select",
        "file",
        "email",
        "phone",
        "currency",
    ]
    required: bool
    options: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")


class WorkflowForm(BaseModel):
    id: str
    node_id: str = Field(alias="nodeId")
    name: str
    fields: list[FormField] = Field(default_factory=list)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class BusinessRule(BaseModel):
    id: str
    name: str
    description: str
    applies_to_node_id: str | None = Field(default=None, alias="appliesToNodeId")
    expression: str
    severity: Literal["info", "warning", "blocking"] = "blocking"

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class Analysis(BaseModel):
    summary: str
    assumptions: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    complexity: Literal["low", "medium", "high"]

    model_config = ConfigDict(extra="forbid")


class TextoAFlujoResponse(BaseModel):
    policy: Policy
    roles: list[Role]
    nodes: list[WorkflowNode]
    transitions: list[Transition]
    forms: list[WorkflowForm]
    business_rules: list[BusinessRule] = Field(alias="businessRules")
    analysis: Analysis

    model_config = ConfigDict(populate_by_name=True, extra="forbid")