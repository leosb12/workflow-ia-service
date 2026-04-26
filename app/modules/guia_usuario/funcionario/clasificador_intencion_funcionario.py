import unicodedata

from app.modules.guia_usuario.comun.solicitud_guia import PantallaGuia
from app.modules.guia_usuario.comun.respuesta_guia import IntencionGuiaFuncionario


class ClasificadorIntencionFuncionario:
    def clasificar_intencion(
        self,
        question: str,
        screen: PantallaGuia,
    ) -> IntencionGuiaFuncionario:
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
            return IntencionGuiaFuncionario.EXPLAIN_SCREEN

        if self._contains_any(
            normalized,
            [
                "que puedo hacer aqui",
                "que puedo hacer",
                "que opciones tengo",
                "que acciones tengo",
            ],
        ):
            return IntencionGuiaFuncionario.WHAT_CAN_I_DO_HERE

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
            return IntencionGuiaFuncionario.PRIORITIZE_TASKS

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
            return IntencionGuiaFuncionario.EXPLAIN_COMPLETION_ERROR

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
            return IntencionGuiaFuncionario.VALIDATE_BEFORE_COMPLETE

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
            return IntencionGuiaFuncionario.EXPLAIN_NEXT_STEP

        if self._contains_any(
            normalized,
            [
                "que significa este formulario",
                "que lleno aqui",
                "como lleno este formulario",
                "explica el formulario",
            ],
        ):
            return IntencionGuiaFuncionario.EXPLAIN_FORM

        if self._contains_any(
            normalized,
            [
                "que significa este campo",
                "que significa el campo",
                "para que sirve este campo",
                "explica este campo",
            ],
        ):
            return IntencionGuiaFuncionario.EXPLAIN_FIELD

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
            return IntencionGuiaFuncionario.HELP_COMPLETE_FORM

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
            return IntencionGuiaFuncionario.EXPLAIN_TASK

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
            return IntencionGuiaFuncionario.EXPLAIN_TASK_STATUS

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
            return IntencionGuiaFuncionario.EXPLAIN_WORKFLOW_PROGRESS

        if self._contains_any(
            normalized,
            [
                "paso a paso",
                "guiame",
                "como hago esto",
                "como empiezo",
            ],
        ):
            return IntencionGuiaFuncionario.GUIDE_STEP_BY_STEP

        if self._contains_any(
            normalized,
            [
                "notificaciones",
                "notificacion",
                "activar notificaciones",
                "chrome",
                "como activo notificaciones",
                "recibo notificaciones",
                "que notificaciones recibo",
            ],
        ):
            return IntencionGuiaFuncionario.EXPLAIN_NOTIFICATIONS

        if screen == PantallaGuia.TASK_FORM and self._contains_any(
            normalized,
            ["formulario", "campo", "observacion"],
        ):
            return IntencionGuiaFuncionario.EXPLAIN_FORM

        if screen == PantallaGuia.TASK_HISTORY and self._contains_any(
            normalized,
            ["tramite", "historial", "progreso"],
        ):
            return IntencionGuiaFuncionario.EXPLAIN_WORKFLOW_PROGRESS

        return IntencionGuiaFuncionario.GENERAL_EMPLOYEE_HELP

    def _contains_any(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", (text or "").lower())
        without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(without_accents.split())

    detect = clasificar_intencion


EmployeeGuideIntentClassifier = ClasificadorIntencionFuncionario
