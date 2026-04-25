import unicodedata

from app.modules.user_guide.common.guide_request import GuideScreen
from app.modules.user_guide.common.guide_response import EmployeeGuideIntent


class EmployeeGuideIntentClassifier:
    def detect(self, question: str, screen: GuideScreen) -> EmployeeGuideIntent:
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
            return EmployeeGuideIntent.EXPLAIN_SCREEN

        if self._contains_any(
            normalized,
            [
                "que puedo hacer aqui",
                "que puedo hacer",
                "que opciones tengo",
                "que acciones tengo",
            ],
        ):
            return EmployeeGuideIntent.WHAT_CAN_I_DO_HERE

        if self._contains_any(
            normalized,
            [
                "que tarea atiendo primero",
                "que tarea hago primero",
                "que conviene atender primero",
                "prioriza mis tareas",
                "cual es la tarea mas urgente",
            ],
        ):
            return EmployeeGuideIntent.PRIORITIZE_TASKS

        if self._contains_any(
            normalized,
            [
                "por que no puedo finalizar",
                "por que no puedo completar",
                "por que da error al finalizar",
                "error al finalizar",
                "error al completar",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_COMPLETION_ERROR

        if self._contains_any(
            normalized,
            [
                "puedo finalizar",
                "puedo completar",
                "que me falta",
                "que falta para finalizar",
                "faltan campos",
                "faltan datos",
            ],
        ):
            return EmployeeGuideIntent.VALIDATE_BEFORE_COMPLETE

        if self._contains_any(
            normalized,
            [
                "que pasa despues",
                "a donde pasa despues",
                "a donde pasa el tramite",
                "si marco si",
                "si marco no",
                "que pasa si marco",
                "siguiente paso del tramite",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_NEXT_STEP

        if self._contains_any(
            normalized,
            [
                "que significa este formulario",
                "que lleno aqui",
                "como lleno este formulario",
                "explica el formulario",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_FORM

        if self._contains_any(
            normalized,
            [
                "que significa este campo",
                "que significa el campo",
                "para que sirve este campo",
                "explica este campo",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_FIELD

        if self._contains_any(
            normalized,
            [
                "ayudame a completar",
                "como lleno",
                "como redacto",
                "ayudame con observaciones",
                "como escribo las observaciones",
            ],
        ):
            return EmployeeGuideIntent.HELP_COMPLETE_FORM

        if self._contains_any(
            normalized,
            [
                "que tarea estoy ejecutando",
                "que debo hacer",
                "explica la tarea",
                "explica esta actividad",
                "que se espera que haga",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_TASK

        if self._contains_any(
            normalized,
            [
                "en que estado esta",
                "estado de la tarea",
                "esta atrasada",
                "esta vencida",
                "por que esta atrasada",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_TASK_STATUS

        if self._contains_any(
            normalized,
            [
                "en que etapa esta",
                "que etapas ya pasaron",
                "que falta del tramite",
                "por que esta detenido",
                "progreso del tramite",
                "historial del tramite",
            ],
        ):
            return EmployeeGuideIntent.EXPLAIN_WORKFLOW_PROGRESS

        if self._contains_any(
            normalized,
            [
                "paso a paso",
                "guiame",
                "como hago esto",
                "como empiezo",
            ],
        ):
            return EmployeeGuideIntent.GUIDE_STEP_BY_STEP

        if screen == GuideScreen.TASK_FORM and self._contains_any(
            normalized,
            ["formulario", "campo", "observacion"],
        ):
            return EmployeeGuideIntent.EXPLAIN_FORM

        if screen == GuideScreen.TASK_HISTORY and self._contains_any(
            normalized,
            ["tramite", "historial", "progreso"],
        ):
            return EmployeeGuideIntent.EXPLAIN_WORKFLOW_PROGRESS

        return EmployeeGuideIntent.GENERAL_EMPLOYEE_HELP

    def _contains_any(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", (text or "").lower())
        without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(without_accents.split())
