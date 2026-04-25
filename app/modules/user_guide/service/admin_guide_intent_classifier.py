import unicodedata

from app.modules.user_guide.schemas.guide_request import GuideScreen
from app.modules.user_guide.schemas.guide_response import AdminGuideIntent


class AdminGuideIntentClassifier:
    def detect(self, question: str, screen: GuideScreen) -> AdminGuideIntent:
        normalized = self._normalize(question)

        if self._contains_any(
            normalized,
            [
                "que hago aqui",
                "donde estoy",
                "explica esta pantalla",
                "para que sirve esta pantalla",
            ],
        ):
            return AdminGuideIntent.EXPLAIN_SCREEN

        if self._contains_any(
            normalized,
            [
                "que puedo hacer aqui",
                "que puedo hacer",
                "que acciones tengo",
                "que opciones tengo",
            ],
        ):
            return AdminGuideIntent.WHAT_CAN_I_DO_HERE

        if self._contains_any(
            normalized,
            [
                "responsable",
                "a quien asigno",
                "quien deberia hacerlo",
                "quien deberia asignar",
            ],
        ):
            return AdminGuideIntent.SUGGEST_RESPONSIBLE

        if self._contains_any(
            normalized,
            [
                "formulario",
                "campo deberia tener",
                "que campo le pongo",
                "sugerime formulario",
                "sugiere formulario",
                "que le pongo",
            ],
        ):
            return AdminGuideIntent.SUGGEST_ACTIVITY_FORM

        if self._contains_any(
            normalized,
            [
                "decision",
                "rama si",
                "rama no",
                "como conecto esta decision",
            ],
        ):
            return AdminGuideIntent.SUGGEST_DECISION

        if self._contains_any(
            normalized,
            [
                "siguiente actividad",
                "que sigue",
                "que actividad sigue",
                "cual seria el siguiente paso",
            ],
        ):
            return AdminGuideIntent.SUGGEST_NEXT_ACTIVITY

        if self._contains_any(
            normalized,
            [
                "puedo activar",
                "esta lista para activar",
                "valida la politica",
                "que me falta",
                "politica incompleta",
            ],
        ):
            return AdminGuideIntent.VALIDATE_POLICY

        if self._contains_any(
            normalized,
            [
                "por que no puedo activar",
                "por que da error",
                "que significa este error",
                "explica este error",
            ],
        ):
            return AdminGuideIntent.EXPLAIN_POLICY_ERROR

        if self._contains_any(
            normalized,
            [
                "paso a paso",
                "guiame",
                "como empiezo",
                "como hago esto",
            ],
        ):
            return AdminGuideIntent.GUIDE_STEP_BY_STEP

        if self._contains_any(
            normalized,
            [
                "optimiza",
                "mejora esta politica",
                "como mejorar",
                "mas eficiente",
            ],
        ):
            return AdminGuideIntent.OPTIMIZE_POLICY

        if self._contains_any(
            normalized,
            [
                "crear politica",
                "nueva politica",
                "como crear una politica",
            ],
        ):
            return AdminGuideIntent.HELP_CREATE_POLICY

        if self._contains_any(
            normalized,
            [
                "activar politica",
                "como activo",
                "como desactivo",
                "como pauso",
            ],
        ):
            return AdminGuideIntent.HELP_ACTIVATE_POLICY

        if screen == GuideScreen.POLICY_DESIGNER and self._contains_any(
            normalized,
            ["ayuda", "orientame", "explicame"],
        ):
            return AdminGuideIntent.EXPLAIN_SCREEN

        return AdminGuideIntent.GENERAL_ADMIN_HELP

    def _contains_any(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", (text or "").lower())
        without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(without_accents.split())
