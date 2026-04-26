from typing import Any, Literal

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


TipoOperacionEdicion = Literal[
    "ADD_NODE",
    "UPDATE_NODE",
    "DELETE_NODE",
    "ADD_TRANSITION",
    "UPDATE_TRANSITION",
    "DELETE_TRANSITION",
    "ASSIGN_RESPONSIBLE",
    "UPDATE_FORM",
    "ADD_FORM_FIELD",
    "DELETE_FORM_FIELD",
    "RENAME_NODE",
    "CREATE_LOOP",
    "UPDATE_DECISION_CONDITION",
    "MOVE_NODE",
    "ADD_BUSINESS_RULE",
    "DELETE_BUSINESS_RULE",
]

IntencionEdicion = Literal[
    "UPDATE_WORKFLOW",
    "NEEDS_CLARIFICATION",
    "UNSUPPORTED_REQUEST",
]


class OperacionEdicionFlujo(BaseModel):
    type: TipoOperacionEdicion
    node_id: str | None = Field(default=None, alias="nodeId")
    node_name: str | None = Field(
        default=None,
        validation_alias=AliasChoices("nodeName", "name", "activityName"),
        serialization_alias="nodeName",
    )
    node_type: str | None = Field(default=None, alias="nodeType")
    description: str | None = None
    old_name: str | None = Field(default=None, alias="oldName")
    new_name: str | None = Field(default=None, alias="newName")
    reference_node_id: str | None = Field(default=None, alias="referenceNodeId")
    reference_node_name: str | None = Field(default=None, alias="referenceNodeName")
    position: Literal["before", "after"] | None = None
    transition_id: str | None = Field(default=None, alias="transitionId")
    transition_label: str | None = Field(
        default=None,
        validation_alias=AliasChoices("transitionLabel", "label"),
        serialization_alias="transitionLabel",
    )
    from_node_id: str | None = Field(default=None, alias="fromNodeId")
    from_node_name: str | None = Field(default=None, alias="fromNodeName")
    to_node_id: str | None = Field(default=None, alias="toNodeId")
    to_node_name: str | None = Field(default=None, alias="toNodeName")
    condition: str | None = None
    responsible_role_id: str | None = Field(default=None, alias="responsibleRoleId")
    responsible_role_name: str | None = Field(default=None, alias="responsibleRoleName")
    responsible_type: Literal["department", "initiator"] | None = Field(default=None, alias="responsibleType")
    department_hint: str | None = Field(default=None, alias="departmentHint")
    form_id: str | None = Field(default=None, alias="formId")
    form_name: str | None = Field(default=None, alias="formName")
    field_id: str | None = Field(default=None, alias="fieldId")
    field_label: str | None = Field(default=None, alias="fieldLabel")
    field_type: str | None = Field(default=None, alias="fieldType")
    required: bool | None = None
    options: list[str] = Field(default_factory=list)
    decision_condition: str | None = Field(default=None, alias="decisionCondition")
    business_rule_id: str | None = Field(default=None, alias="businessRuleId")
    business_rule_name: str | None = Field(default=None, alias="businessRuleName")
    expression: str | None = None
    severity: Literal["info", "warning", "blocking"] | None = None
    reason: str | None = None
    payload: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class RespuestaEdicionFlujo(BaseModel):
    success: bool
    intent: IntencionEdicion
    summary: str = Field(min_length=1, max_length=500)
    operations: list[OperacionEdicionFlujo] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    errors: list[str] = Field(default_factory=list)
    requires_confirmation: bool = Field(alias="requiresConfirmation")

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "intent": "UPDATE_WORKFLOW",
                    "summary": "Se agregara un loop desde Revisar solicitud hacia Solicitar datos.",
                    "operations": [
                        {
                            "type": "ADD_TRANSITION",
                            "fromNodeName": "Revisar solicitud",
                            "toNodeName": "Solicitar datos",
                            "condition": "Informacion incompleta",
                        }
                    ],
                    "warnings": [],
                    "errors": [],
                    "requiresConfirmation": True,
                }
            ]
        },
    )


WorkflowEditOperation = OperacionEdicionFlujo
WorkflowEditResponse = RespuestaEdicionFlujo

