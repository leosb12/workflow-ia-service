from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class FormFieldSchema(BaseModel):
    id: str = Field(min_length=1, max_length=120)
    label: str = Field(min_length=1, max_length=200)
    type: Literal["text", "textarea", "number", "boolean", "select", "date", "file"]
    required: bool
    options: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="forbid")

    @field_validator("options")
    @classmethod
    def validate_options(cls, value: list[str]) -> list[str]:
        return [item.strip() for item in value if item and item.strip()]

    @model_validator(mode="after")
    def validate_select_options(self) -> "FormFieldSchema":
        if self.type == "select" and not self.options:
            raise ValueError("Los campos select deben incluir options")
        return self


class FormFillContext(BaseModel):
    model_config = ConfigDict(extra="allow")


class FormFillRequest(BaseModel):
    activity_id: str = Field(alias="activityId", min_length=1, max_length=120)
    activity_name: str = Field(alias="activityName", min_length=1, max_length=200)
    policy_name: str = Field(alias="policyName", min_length=1, max_length=200)
    form_schema: list[FormFieldSchema] = Field(alias="formSchema", min_length=1)
    current_values: dict[str, Any] = Field(alias="currentValues", default_factory=dict)
    user_prompt: str = Field(alias="userPrompt", min_length=1, max_length=4000)
    context: dict[str, Any] | None = None

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "activityId": "task_legal_1",
                    "activityName": "Revision legal",
                    "policyName": "Instalacion de medidor",
                    "formSchema": [
                        {
                            "id": "decision",
                            "label": "Decision",
                            "type": "select",
                            "required": True,
                            "options": ["aprobado", "rechazado", "observado"],
                        },
                        {
                            "id": "observations",
                            "label": "Observaciones",
                            "type": "textarea",
                            "required": False,
                            "options": [],
                        },
                        {
                            "id": "requiresDocuments",
                            "label": "Requiere documentos adicionales",
                            "type": "boolean",
                            "required": False,
                            "options": [],
                        },
                    ],
                    "currentValues": {
                        "decision": None,
                        "observations": "",
                        "requiresDocuments": None,
                    },
                    "userPrompt": "Rechaza la solicitud y pon una explicacion de que faltan documentos legales.",
                    "context": {
                        "tramiteId": "tramite_001",
                        "currentDepartment": "Legal",
                        "userRole": "funcionario",
                    },
                }
            ]
        },
    )

    @field_validator("user_prompt")
    @classmethod
    def normalize_prompt(cls, value: str) -> str:
        normalized = value.strip()
        if not normalized:
            raise ValueError("El prompt del usuario es obligatorio")
        return normalized

    @model_validator(mode="after")
    def validate_schema_and_values(self) -> "FormFillRequest":
        field_ids = [field.id for field in self.form_schema]
        if len(field_ids) != len(set(field_ids)):
            raise ValueError("formSchema no puede tener ids duplicados")

        unknown_keys = [key for key in self.current_values.keys() if key not in set(field_ids)]
        if unknown_keys:
            raise ValueError(
                f"currentValues contiene campos inexistentes en formSchema: {', '.join(sorted(unknown_keys))}"
            )

        return self
