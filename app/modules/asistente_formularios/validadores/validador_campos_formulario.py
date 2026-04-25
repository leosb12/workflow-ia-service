import re
import unicodedata
from dataclasses import dataclass
from datetime import date
from typing import Any

from starlette.status import HTTP_400_BAD_REQUEST

from app.core.exceptions import ApiException
from app.modules.asistente_formularios.modelos.solicitud_llenado_formulario import FormFieldSchema


@dataclass
class ResultadoSaneado:
    updated_values: dict[str, Any]
    warnings: list[str]


class ValidadorCamposFormulario:
    def index_fields(self, fields: list[FormFieldSchema]) -> dict[str, FormFieldSchema]:
        indexed: dict[str, FormFieldSchema] = {}
        for field in fields:
            if field.id in indexed:
                raise ApiException(HTTP_400_BAD_REQUEST, f"formSchema contiene fieldId duplicado: {field.id}")
            indexed[field.id] = field
        return indexed

    def build_base_values(
        self,
        fields: list[FormFieldSchema],
        current_values: dict[str, Any],
    ) -> dict[str, Any]:
        base: dict[str, Any] = {}
        for field in fields:
            base[field.id] = current_values.get(field.id)
        return base

    def sanitize_updated_values(
        self,
        *,
        fields: list[FormFieldSchema],
        base_values: dict[str, Any],
        candidate_values: dict[str, Any] | None,
    ) -> ResultadoSaneado:
        normalized = dict(base_values)
        warnings: list[str] = []
        field_map = self.index_fields(fields)

        if not candidate_values:
            return ResultadoSaneado(updated_values=normalized, warnings=warnings)

        for field_id, value in candidate_values.items():
            schema = field_map.get(field_id)
            if schema is None:
                warnings.append(f"Se ignoro el campo inexistente '{field_id}'.")
                continue

            sanitized_value, field_warning = self._sanitize_value(schema, value, base_values.get(field_id))
            if field_warning:
                warnings.append(field_warning)
                continue

            normalized[field_id] = sanitized_value

        return ResultadoSaneado(updated_values=normalized, warnings=self._deduplicate(warnings))

    def _sanitize_value(
        self,
        field: FormFieldSchema,
        value: Any,
        current_value: Any,
    ) -> tuple[Any, str | None]:
        if value is None:
            return None, None

        if field.type in {"text", "textarea"}:
            if isinstance(value, str):
                normalized = value.strip()
                return normalized, None
            return current_value, f"No se pudo normalizar '{field.id}' como texto."

        if field.type == "number":
            if isinstance(value, bool):
                return current_value, f"No se pudo normalizar '{field.id}' como numero."
            if isinstance(value, (int, float)):
                return value, None
            if isinstance(value, str):
                raw = value.strip().replace(",", ".")
                try:
                    parsed = float(raw)
                except ValueError:
                    return current_value, f"No se pudo normalizar '{field.id}' como numero."
                return int(parsed) if parsed.is_integer() else parsed, None
            return current_value, f"No se pudo normalizar '{field.id}' como numero."

        if field.type == "boolean":
            parsed = self._parse_boolean(value)
            if parsed is None:
                return current_value, f"No se pudo normalizar '{field.id}' como boolean."
            return parsed, None

        if field.type == "select":
            if not isinstance(value, str):
                return current_value, f"No se pudo normalizar '{field.id}' como seleccion."
            mapped = self._match_option(value, field.options)
            if mapped is None:
                return current_value, f"El valor propuesto para '{field.id}' no coincide con ninguna opcion valida."
            return mapped, None

        if field.type == "date":
            normalized_date = self._parse_date(value)
            if normalized_date is None:
                return current_value, f"No se pudo normalizar '{field.id}' como fecha ISO."
            return normalized_date, None

        if field.type == "file":
            return current_value, f"El campo '{field.id}' es tipo file y no se completa automaticamente."

        return current_value, f"Tipo de campo no soportado para '{field.id}'."

    def _parse_boolean(self, value: Any) -> bool | None:
        if isinstance(value, bool):
            return value
        if isinstance(value, (int, float)) and value in {0, 1}:
            return bool(value)
        if not isinstance(value, str):
            return None

        normalized = self._normalize_text(value)
        truthy = {"true", "1", "si", "sí", "yes", "aprobado", "aprobar", "viable", "requiere"}
        falsy = {"false", "0", "no", "rechazado", "rechazar", "no_viable", "inviable", "no_requiere"}

        if normalized in truthy:
            return True
        if normalized in falsy:
            return False
        return None

    def _parse_date(self, value: Any) -> str | None:
        if isinstance(value, str):
            raw = value.strip()
            candidate = raw.split("T", maxsplit=1)[0]
            try:
                return date.fromisoformat(candidate).isoformat()
            except ValueError:
                return None
        return None

    def _match_option(self, proposed: str, options: list[str]) -> str | None:
        proposed_normalized = self._normalize_text(proposed)
        for option in options:
            if self._normalize_text(option) == proposed_normalized:
                return option

        aliases = {
            "aprobado": {"aprobar", "aprobada", "aprobado", "aceptado", "viable", "si"},
            "rechazado": {"rechazar", "rechazado", "rechazada", "denegado", "no viable", "inviable", "no"},
            "observado": {"observado", "observar", "observacion", "observacion breve", "observada"},
        }

        for option in options:
            option_normalized = self._normalize_text(option)
            for canonical, values in aliases.items():
                if option_normalized == self._normalize_text(canonical) and proposed_normalized in {
                    self._normalize_text(item) for item in values
                }:
                    return option

        for option in options:
            option_normalized = self._normalize_text(option)
            if proposed_normalized in option_normalized or option_normalized in proposed_normalized:
                return option

        return None

    def _normalize_text(self, value: str) -> str:
        normalized = unicodedata.normalize("NFKD", value.strip().lower())
        normalized = normalized.encode("ascii", "ignore").decode("ascii")
        normalized = re.sub(r"[^a-z0-9]+", " ", normalized)
        return " ".join(normalized.split())

    def _deduplicate(self, values: list[str]) -> list[str]:
        seen: set[str] = set()
        ordered: list[str] = []
        for value in values:
            key = value.strip()
            if key and key not in seen:
                seen.add(key)
                ordered.append(key)
        return ordered


SanitizedResult = ResultadoSaneado
FormFieldValidator = ValidadorCamposFormulario
