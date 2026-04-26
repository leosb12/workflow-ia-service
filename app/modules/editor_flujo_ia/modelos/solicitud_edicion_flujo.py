from typing import Any

from pydantic import AliasChoices, BaseModel, ConfigDict, Field


class SolicitudEdicionFlujo(BaseModel):
    workflow: dict[str, Any] = Field(
        validation_alias=AliasChoices("workflow", "currentWorkflow", "flujoActual"),
        min_length=1,
    )
    prompt: str = Field(
        validation_alias=AliasChoices("prompt", "userPrompt", "instruction", "instruccion"),
        min_length=1,
        max_length=6000,
    )
    context: dict[str, Any] = Field(default_factory=dict)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


WorkflowEditRequest = SolicitudEdicionFlujo

