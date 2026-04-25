from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class FormFieldChange(BaseModel):
    field_id: str = Field(alias="fieldId", min_length=1)
    old_value: Any = Field(alias="oldValue", default=None)
    new_value: Any = Field(alias="newValue", default=None)
    reason: str = Field(min_length=1, max_length=300)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class FormFillResponse(BaseModel):
    success: bool = True
    updated_values: dict[str, Any] = Field(alias="updatedValues", default_factory=dict)
    changes: list[FormFieldChange] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    confidence: float = Field(ge=0.0, le=1.0)
    message: str = Field(min_length=1, max_length=200)

    model_config = ConfigDict(
        populate_by_name=True,
        extra="forbid",
        json_schema_extra={
            "examples": [
                {
                    "success": True,
                    "updatedValues": {
                        "decision": "rechazado",
                        "observations": (
                            "La solicitud fue rechazada debido a la falta de documentos legales "
                            "requeridos para continuar con el tramite."
                        ),
                        "requiresDocuments": True,
                    },
                    "changes": [
                        {
                            "fieldId": "decision",
                            "oldValue": None,
                            "newValue": "rechazado",
                            "reason": "El usuario solicito rechazar la solicitud.",
                        },
                        {
                            "fieldId": "observations",
                            "oldValue": "",
                            "newValue": (
                                "La solicitud fue rechazada debido a la falta de documentos legales "
                                "requeridos para continuar con el tramite."
                            ),
                            "reason": "Se genero una observacion breve y formal.",
                        },
                    ],
                    "warnings": [],
                    "confidence": 0.92,
                    "message": "Formulario actualizado correctamente con IA.",
                }
            ]
        },
    )
