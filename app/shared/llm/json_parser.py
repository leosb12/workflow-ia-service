import json
from json import JSONDecodeError
from typing import Any

from starlette.status import HTTP_502_BAD_GATEWAY

from app.core.exceptions import ApiException


class JsonObjectParser:
    def parse(self, raw_json: str) -> dict[str, Any]:
        if not raw_json or not raw_json.strip():
            raise ApiException(
                HTTP_502_BAD_GATEWAY,
                "DeepSeek devolvio JSON vacio",
            )

        normalized = raw_json.strip()

        if normalized.startswith("```"):
            normalized = self._limpiar_bloque_markdown(normalized)

        try:
            parsed = json.loads(normalized)
        except JSONDecodeError as exc:
            extracted = self._extraer_primer_objeto_json(normalized)
            if extracted is None:
                raise ApiException(
                    HTTP_502_BAD_GATEWAY,
                    "DeepSeek devolvio JSON invalido",
                ) from exc

            try:
                parsed = json.loads(extracted)
            except JSONDecodeError as second_exc:
                raise ApiException(
                    HTTP_502_BAD_GATEWAY,
                    "DeepSeek devolvio JSON invalido",
                ) from second_exc

        if not isinstance(parsed, dict) or not parsed:
            raise ApiException(
                HTTP_502_BAD_GATEWAY,
                "DeepSeek devolvio un objeto JSON vacio o invalido",
            )

        return parsed

    def _limpiar_bloque_markdown(self, raw: str) -> str:
        lines = raw.splitlines()
        if len(lines) >= 2 and lines[0].strip().startswith("```"):
            if lines[-1].strip() == "```":
                return "\n".join(lines[1:-1]).strip()
        return raw

    def _extraer_primer_objeto_json(self, raw: str) -> str | None:
        start = raw.find("{")
        end = raw.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return raw[start : end + 1]
