from __future__ import annotations

from app.modules.guia_usuario.comun.solicitud_guia import (
    EmployeeFormContext,
    EmployeeFormFieldContext,
    EmployeeGuideRequest,
    EmployeeNextPossibleStepContext,
    GuideScreen,
)
from app.modules.guia_usuario.comun.respuesta_guia import (
    EmployeeFormHelp,
    EmployeeGuideIntent,
    EmployeeGuideResponse,
    EmployeeMissingField,
    EmployeePrioritySuggestion,
    GuideSeverity,
    SuggestedAction,
)


class RespaldoGuiaFuncionario:
    def construir_respuesta(
        self,
        request: EmployeeGuideRequest,
        intent: EmployeeGuideIntent,
    ) -> EmployeeGuideResponse:
        special_response = self._build_special_response(request, intent)
        if special_response is not None:
            return special_response

        missing_fields = self._build_missing_fields(request.context.form)
        form_help = self._build_form_help(request.context.form)
        priority_suggestion = self._build_priority_suggestion(request)
        next_step_explanation = self._build_next_step_explanation(request.context.next_possible_steps)
        suggested_actions = self._build_suggested_actions(request, missing_fields)

        if intent == EmployeeGuideIntent.EXPLAIN_FORM:
            return EmployeeGuideResponse(
                answer=self._build_form_answer(request),
                steps=self._build_form_steps(request),
                formHelp=form_help,
                missingFields=missing_fields,
                suggestedActions=suggested_actions,
                severity=GuideSeverity.ERROR if missing_fields else GuideSeverity.INFO,
                intent=intent,
            )

        if intent == EmployeeGuideIntent.EXPLAIN_FIELD:
            return EmployeeGuideResponse(
                answer=self._build_field_answer(request, form_help),
                steps=self._build_form_steps(request)[:2],
                formHelp=form_help[:2],
                missingFields=missing_fields[:1],
                suggestedActions=suggested_actions[:2],
                severity=GuideSeverity.ERROR if missing_fields else GuideSeverity.INFO,
                intent=intent,
            )

        if intent == EmployeeGuideIntent.HELP_COMPLETE_FORM:
            return EmployeeGuideResponse(
                answer=self._build_complete_form_answer(request, missing_fields),
                steps=self._build_complete_form_steps(request, missing_fields),
                formHelp=form_help,
                missingFields=missing_fields,
                suggestedActions=suggested_actions,
                severity=GuideSeverity.ERROR if missing_fields else GuideSeverity.INFO,
                intent=intent,
            )

        if intent in {
            EmployeeGuideIntent.VALIDATE_BEFORE_COMPLETE,
            EmployeeGuideIntent.EXPLAIN_COMPLETION_ERROR,
        }:
            return EmployeeGuideResponse(
                answer=self._build_completion_answer(request, missing_fields),
                steps=self._build_complete_form_steps(request, missing_fields),
                formHelp=form_help[:2],
                missingFields=missing_fields,
                nextStepExplanation=next_step_explanation if not missing_fields else None,
                suggestedActions=suggested_actions,
                severity=self._completion_severity(request, missing_fields),
                intent=intent,
            )

        if intent == EmployeeGuideIntent.PRIORITIZE_TASKS:
            return EmployeeGuideResponse(
                answer=self._build_priority_answer(request, priority_suggestion),
                steps=self._build_priority_steps(request),
                prioritySuggestion=priority_suggestion,
                suggestedActions=suggested_actions,
                severity=GuideSeverity.WARNING if priority_suggestion else GuideSeverity.INFO,
                intent=intent,
            )

        if intent == EmployeeGuideIntent.EXPLAIN_NEXT_STEP:
            return EmployeeGuideResponse(
                answer=self._build_next_step_answer(request, next_step_explanation),
                steps=self._build_next_step_steps(request),
                nextStepExplanation=next_step_explanation,
                suggestedActions=suggested_actions[:2],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        if intent == EmployeeGuideIntent.EXPLAIN_TASK_STATUS:
            return EmployeeGuideResponse(
                answer=self._build_task_status_answer(request),
                steps=self._build_task_status_steps(request),
                missingFields=missing_fields[:1],
                suggestedActions=suggested_actions[:2],
                severity=self._task_status_severity(request),
                intent=intent,
            )

        if intent == EmployeeGuideIntent.EXPLAIN_WORKFLOW_PROGRESS:
            return EmployeeGuideResponse(
                answer=self._build_progress_answer(request),
                steps=self._build_progress_steps(request),
                nextStepExplanation=next_step_explanation,
                suggestedActions=suggested_actions[:2],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        if intent == EmployeeGuideIntent.EXPLAIN_TASK:
            return EmployeeGuideResponse(
                answer=self._build_task_answer(request),
                steps=self._build_task_steps(request),
                formHelp=form_help[:2],
                nextStepExplanation=next_step_explanation,
                suggestedActions=suggested_actions[:3],
                severity=self._task_status_severity(request),
                intent=intent,
            )

        if intent in {
            EmployeeGuideIntent.EXPLAIN_SCREEN,
            EmployeeGuideIntent.WHAT_CAN_I_DO_HERE,
            EmployeeGuideIntent.GUIDE_STEP_BY_STEP,
        }:
            return EmployeeGuideResponse(
                answer=self._build_screen_answer(request),
                steps=self._build_screen_steps(request, intent),
                prioritySuggestion=priority_suggestion if request.screen == GuideScreen.EMPLOYEE_DASHBOARD else None,
                suggestedActions=suggested_actions[:3],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        return EmployeeGuideResponse(
            answer=self._build_general_help_answer(request),
            steps=self._build_general_help_steps(request),
            formHelp=form_help[:2],
            prioritySuggestion=priority_suggestion if request.screen == GuideScreen.EMPLOYEE_DASHBOARD else None,
            suggestedActions=suggested_actions[:3],
            severity=self._task_status_severity(request),
            intent=intent,
        )

    def _build_form_help(self, form: EmployeeFormContext | None) -> list[EmployeeFormHelp]:
        if form is None:
            return []

        return [
            EmployeeFormHelp(field=field.name, help=self._field_help_text(field))
            for field in form.fields[:6]
        ]

    def _build_missing_fields(self, form: EmployeeFormContext | None) -> list[EmployeeMissingField]:
        if form is None or not form.missing_required_fields:
            return []

        fields_by_name = {field.name: field for field in form.fields}
        items: list[EmployeeMissingField] = []
        for field_name in form.missing_required_fields[:6]:
            field = fields_by_name.get(field_name)
            label = field.label if field else field_name
            items.append(
                EmployeeMissingField(
                    field=field_name,
                    message=f"Debes completar {label} antes de finalizar la tarea.",
                )
            )
        return items

    def _build_priority_suggestion(
        self,
        request: EmployeeGuideRequest,
    ) -> EmployeePrioritySuggestion | None:
        queue = request.context.task_queue
        if not queue:
            return None

        ordered = sorted(
            queue,
            key=lambda item: (
                0 if item.overdue else 1,
                0 if (item.priority or "").upper() == "HIGH" else 1,
                -(item.age_hours or 0),
            ),
        )
        top = ordered[0]

        reason = "Es la tarea más conveniente para avanzar primero."
        if top.overdue:
            reason = "Esta tarea está atrasada y conviene atenderla primero para evitar más demora."
        elif (top.priority or "").upper() == "HIGH":
            reason = "Esta tarea tiene prioridad alta dentro de tu bandeja."
        elif (top.age_hours or 0) >= 24:
            reason = "Esta tarea lleva tiempo pendiente y conviene resolverla antes que las más recientes."

        return EmployeePrioritySuggestion(
            recommendedTaskId=top.task_id,
            reason=reason,
        )

    def _build_next_step_explanation(
        self,
        next_steps: list[EmployeeNextPossibleStepContext],
    ) -> str | None:
        if not next_steps:
            return None

        parts: list[str] = []
        for step in next_steps[:4]:
            condition = (step.condition or "Al finalizar").strip()
            next_node = (step.next_node or "el siguiente paso del flujo").strip()
            next_department = f" en {step.next_department}" if step.next_department else ""
            parts.append(f"{condition}, el trámite pasará a {next_node}{next_department}.")

        return " ".join(parts)

    def _build_suggested_actions(
        self,
        request: EmployeeGuideRequest,
        missing_fields: list[EmployeeMissingField],
    ) -> list[SuggestedAction]:
        actions: list[SuggestedAction] = []
        available_actions = set(request.context.available_actions)

        def add_action(action: str, label: str) -> None:
            if any(item.action == action for item in actions):
                return
            actions.append(SuggestedAction(action=action, label=label))

        if missing_fields:
            add_action("COMPLETE_REQUIRED_FIELDS", "Completar campos obligatorios")
        if "START_TASK" in available_actions:
            add_action("START_TASK", "Tomar o iniciar tarea")
        if "SAVE_FORM" in available_actions:
            add_action("SAVE_FORM", "Guardar avance del formulario")
        if "COMPLETE_TASK" in available_actions:
            add_action("COMPLETE_TASK", "Finalizar tarea")
        if "FILL_FORM_WITH_AI" in available_actions:
            add_action("FILL_FORM_WITH_AI", "Completar formulario con IA")

        return actions[:5]

    def _build_screen_answer(self, request: EmployeeGuideRequest) -> str:
        if request.screen == GuideScreen.PERFIL_USUARIO:
            return (
                "Estas en tu perfil. Aqui puedes revisar los datos de tu cuenta, ver tu departamento "
                "y cambiar tu contrasena."
            )

        if request.screen == GuideScreen.EMPLOYEE_DASHBOARD:
            summary = request.context.dashboard_summary
            pending = summary.pending_tasks if summary else 0
            in_progress = summary.in_progress_tasks if summary else 0
            completed = summary.completed_tasks if summary else 0
            overdue = summary.overdue_tasks if summary else 0
            return (
                "Estás en tu bandeja de trabajo. Aquí puedes revisar tus tareas pendientes, en proceso y completadas. "
                f"Ahora mismo tienes {pending} pendiente(s), {in_progress} en proceso, {completed} completada(s) y {overdue} atrasada(s)."
            )

        if request.screen == GuideScreen.TASK_FORM:
            task_name = request.context.current_node.name if request.context.current_node else "esta tarea"
            return (
                f"Estás completando el formulario de {task_name}. Aquí debes revisar los campos obligatorios, "
                "guardar avances y finalizar solo cuando la información esté completa."
            )

        if request.screen == GuideScreen.TASK_HISTORY:
            return (
                "Estás viendo el seguimiento del trámite. Aquí puedes revisar en qué etapa va, qué pasos ya se completaron y qué falta para cerrar el flujo."
            )

        return (
            "Estás en el detalle operativo de tu tarea. Aquí puedes revisar la actividad actual, el trámite asociado y lo que debes completar para avanzar."
        )

    def _build_screen_steps(
        self,
        request: EmployeeGuideRequest,
        intent: EmployeeGuideIntent,
    ) -> list[str]:
        if request.screen == GuideScreen.PERFIL_USUARIO:
            return [
                "Revisa el resumen de tu cuenta.",
                "Consulta tu departamento dentro del perfil.",
                "Usa la seccion de seguridad para cambiar tu contrasena.",
            ]

        if request.screen == GuideScreen.EMPLOYEE_DASHBOARD:
            steps = [
                "Revisa primero las tareas atrasadas o con prioridad alta.",
                "Abre la tarea que quieras atender para ver su detalle.",
                "Si una tarea ya está en proceso, termina sus campos antes de saltar a otra.",
            ]
            if intent == EmployeeGuideIntent.GUIDE_STEP_BY_STEP:
                return steps
            return steps[:2]

        if request.screen == GuideScreen.TASK_FORM:
            return [
                "Lee el nombre de la actividad y el objetivo del formulario.",
                "Completa primero los campos obligatorios.",
                "Guarda avances o finaliza cuando ya no falte información.",
            ]

        if request.screen == GuideScreen.TASK_HISTORY:
            return [
                "Revisa la etapa actual del trámite.",
                "Identifica qué pasos ya se completaron.",
                "Confirma cuál es el siguiente paso del flujo.",
            ]

        return [
            "Revisa la actividad actual.",
            "Completa el formulario o las observaciones necesarias.",
            "Finaliza cuando toda la información esté validada.",
        ]

    def _build_task_answer(self, request: EmployeeGuideRequest) -> str:
        current_node = request.context.current_node
        if current_node and current_node.name:
            description = current_node.description or "Debes ejecutar esta actividad operativa y registrar el resultado correctamente."
            return f"Estás trabajando en {current_node.name}. {description}"
        return "Debes revisar la actividad actual, completar el formulario correspondiente y registrar el resultado antes de finalizar."

    def _build_task_steps(self, request: EmployeeGuideRequest) -> list[str]:
        steps = [
            "Confirma el objetivo de la actividad actual.",
            "Revisa si ya tienes todos los datos necesarios.",
            "Completa el formulario y valida el resultado antes de finalizar.",
        ]
        if request.context.next_possible_steps:
            steps.append("Verifica qué camino seguirá el trámite después de tu decisión.")
        return steps[:4]

    def _build_form_answer(self, request: EmployeeGuideRequest) -> str:
        current_node = request.context.current_node
        if current_node and current_node.name:
            return (
                f"Este formulario corresponde a {current_node.name}. Debes llenarlo con la información mínima necesaria para que el trámite pueda avanzar sin errores."
            )
        return "Debes completar este formulario con los datos requeridos para que la actividad pueda avanzar correctamente."

    def _build_form_steps(self, request: EmployeeGuideRequest) -> list[str]:
        steps = [
            "Lee el objetivo de la actividad antes de completar el formulario.",
            "Llena primero los campos obligatorios y después las observaciones útiles.",
            "Guarda o finaliza solo cuando la información sea consistente con el resultado de tu revisión.",
        ]
        if request.context.form and request.context.form.missing_required_fields:
            steps.insert(1, "Revisa los campos obligatorios que todavía siguen vacíos.")
        return steps[:4]

    def _build_field_answer(
        self,
        request: EmployeeGuideRequest,
        form_help: list[EmployeeFormHelp],
    ) -> str:
        if form_help:
            return f"El campo {form_help[0].field} se usa así: {form_help[0].help}"
        return "Te explico el campo según su objetivo dentro del formulario actual."

    def _build_complete_form_answer(
        self,
        request: EmployeeGuideRequest,
        missing_fields: list[EmployeeMissingField],
    ) -> str:
        if missing_fields:
            return "Todavía te faltan campos obligatorios. Completa primero esos datos antes de intentar finalizar la tarea."
        if any(field.name.lower().startswith("observ") for field in (request.context.form.fields if request.context.form else [])):
            return "Puedes usar observaciones para dejar contexto claro, resultado de la revisión y cualquier hallazgo importante para el siguiente responsable."
        return "Completa el formulario con información clara, breve y útil para que el siguiente paso del trámite no tenga dudas."

    def _build_complete_form_steps(
        self,
        request: EmployeeGuideRequest,
        missing_fields: list[EmployeeMissingField],
    ) -> list[str]:
        if missing_fields:
            return [
                "Completa primero los campos obligatorios señalados.",
                "Revisa si tus respuestas son consistentes con la actividad.",
                "Vuelve a intentar finalizar cuando ya no falte información.",
            ]
        return [
            "Revisa todos los campos antes de guardar o finalizar.",
            "Usa observaciones para dejar contexto útil.",
            "Finaliza la tarea cuando la información esté completa.",
        ]

    def _build_completion_answer(
        self,
        request: EmployeeGuideRequest,
        missing_fields: list[EmployeeMissingField],
    ) -> str:
        if missing_fields:
            missing_labels = ", ".join(item.field for item in missing_fields[:3])
            return f"No puedes finalizar todavía. Faltan datos obligatorios en: {missing_labels}."

        if request.context.task_status == "PENDING" and "START_TASK" in request.context.available_actions:
            return "Antes de finalizar, primero debes tomar o iniciar la tarea para trabajarla correctamente."

        return "La tarea parece lista para finalizar. Haz una última revisión de campos y observaciones antes de completar la actividad."

    def _completion_severity(
        self,
        request: EmployeeGuideRequest,
        missing_fields: list[EmployeeMissingField],
    ) -> GuideSeverity:
        if missing_fields:
            return GuideSeverity.ERROR
        if request.context.task_status == "OVERDUE":
            return GuideSeverity.WARNING
        return GuideSeverity.SUCCESS

    def _task_status_severity(self, request: EmployeeGuideRequest) -> GuideSeverity:
        task_status = (request.context.task_status or "").upper()
        if task_status == "OVERDUE":
            return GuideSeverity.WARNING
        if task_status == "COMPLETED":
            return GuideSeverity.SUCCESS
        return GuideSeverity.INFO

    def _build_priority_answer(
        self,
        request: EmployeeGuideRequest,
        priority_suggestion: EmployeePrioritySuggestion | None,
    ) -> str:
        if priority_suggestion and priority_suggestion.recommended_task_id:
            return (
                f"Te conviene atender primero la tarea {priority_suggestion.recommended_task_id}. {priority_suggestion.reason}"
            )
        return "Revisa primero las tareas atrasadas, luego las de prioridad alta y después las más antiguas que sigan pendientes."

    def _build_priority_steps(self, request: EmployeeGuideRequest) -> list[str]:
        return [
            "Atiende primero las tareas atrasadas.",
            "Luego prioriza las tareas de prioridad alta.",
            "Si varias tareas tienen el mismo nivel, comienza por la más antigua.",
        ]

    def _build_next_step_answer(
        self,
        request: EmployeeGuideRequest,
        next_step_explanation: str | None,
    ) -> str:
        if next_step_explanation:
            return f"Después de esta actividad, el flujo seguirá así: {next_step_explanation}"
        return "El siguiente paso depende de las condiciones configuradas para esta actividad y del resultado que registres."

    def _build_next_step_steps(self, request: EmployeeGuideRequest) -> list[str]:
        return [
            "Confirma qué resultado o decisión estás registrando.",
            "Revisa a qué nodo o departamento lleva cada condición.",
            "Completa la tarea solo cuando el resultado represente correctamente tu revisión.",
        ]

    def _build_task_status_answer(self, request: EmployeeGuideRequest) -> str:
        task_status = request.context.task_status or "PENDING"
        if task_status == "OVERDUE":
            return "Tu tarea está atrasada. Conviene revisarla cuanto antes para evitar más demora en el trámite."
        if task_status == "IN_PROGRESS":
            return "Tu tarea está en proceso. Lo ideal es terminarla antes de pasar a otra para no dejar trabajo a medias."
        if task_status == "COMPLETED":
            return "Esta tarea ya fue completada correctamente."
        return "Tu tarea sigue pendiente. Debes iniciarla o completarla según el estado actual del trámite."

    def _build_task_status_steps(self, request: EmployeeGuideRequest) -> list[str]:
        return [
            "Confirma el estado actual de la tarea.",
            "Revisa si ya fue iniciada o si aún falta tomarla.",
            "Completa los datos pendientes para avanzar el trámite.",
        ]

    def _build_progress_answer(self, request: EmployeeGuideRequest) -> str:
        summary = request.context.history_summary
        if summary and summary.current_step:
            return (
                f"El trámite está en la etapa {summary.current_step}. Ya se completaron {summary.completed_steps} paso(s) y quedan {summary.pending_steps} pendiente(s)."
            )
        return "Te puedo explicar en qué etapa va el trámite, qué ya pasó y qué falta para completarlo."

    def _build_progress_steps(self, request: EmployeeGuideRequest) -> list[str]:
        steps = [
            "Revisa la etapa actual del trámite.",
            "Confirma qué pasos ya fueron completados.",
            "Verifica cuál será el siguiente paso después de tu tarea.",
        ]
        if request.context.history_summary and request.context.history_summary.last_completed_by:
            steps.append(
                f"El último paso fue completado por {request.context.history_summary.last_completed_by}."
            )
        return steps[:4]

    def _build_general_help_answer(self, request: EmployeeGuideRequest) -> str:
        return (
            "Puedo ayudarte a entender tu tarea, explicar el formulario, validar qué falta antes de finalizar y decirte qué pasa después en el flujo."
        )

    def _build_general_help_steps(self, request: EmployeeGuideRequest) -> list[str]:
        return [
            "Pregúntame qué debes hacer en esta pantalla.",
            "Pregúntame qué campo te falta o qué significa el formulario.",
            "Pregúntame qué pasa después o qué tarea conviene atender primero.",
        ]

    def _field_help_text(self, field: EmployeeFormFieldContext) -> str:
        field_type = (field.type or "").upper()
        label = field.label
        if field_type == "BOOLEAN":
            return f"Marca Sí o No según el resultado real de {label}."
        if field_type == "TEXTAREA":
            return f"Usa {label} para dejar observaciones claras, hallazgos y contexto útil para el siguiente paso."
        if field_type == "FILE":
            return f"Adjunta en {label} la evidencia o documento necesario para respaldar la tarea."
        if field_type == "DATE":
            return f"Indica en {label} la fecha que corresponda al registro o validación realizada."
        if field_type == "NUMBER":
            return f"Completa {label} con un valor numérico válido."
        return f"Completa {label} con la información solicitada para esta actividad."
    def _build_special_response(
        self,
        request: EmployeeGuideRequest,
        intent: EmployeeGuideIntent,
    ) -> EmployeeGuideResponse | None:
        normalized_question = self._normalize(request.question)

        if self._contains_any(
            normalized_question,
            ["olvide mi contrasena", "olvide la contrasena", "no recuerdo mi contrasena"],
        ):
            return EmployeeGuideResponse(
                answer=(
                    "Si olvidaste tu contrasena, en la pantalla de login debes presionar "
                    "'Olvidaste tu contrasena?' para iniciar la recuperacion."
                ),
                steps=[
                    "Ve a la pantalla de login.",
                    "Presiona 'Olvidaste tu contrasena?'.",
                    "Sigue los pasos de recuperacion para restablecer el acceso.",
                ],
                suggestedActions=[],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        if self._contains_any(
            normalized_question,
            [
                "cambiar contrasena",
                "cambio de contrasena",
                "donde cambio mi contrasena",
                "donde cambiar contrasena",
            ],
        ):
            return EmployeeGuideResponse(
                answer="El cambio de contrasena se realiza entrando a tu perfil.",
                steps=[
                    "Abre tu perfil.",
                    "Entra a la seccion de seguridad.",
                    "Completa tu contrasena actual y la nueva contrasena.",
                ],
                suggestedActions=[],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        if self._contains_any(
            normalized_question,
            [
                "mi departamento",
                "ver mi departamento",
                "donde veo mi departamento",
                "cual es mi departamento",
            ],
        ):
            return EmployeeGuideResponse(
                answer="Para ver tu departamento, entra a tu perfil. Ahi aparece en el resumen de tu cuenta.",
                steps=[
                    "Abre tu perfil.",
                    "Busca el resumen de tu cuenta.",
                    "Revisa el campo Departamento.",
                ],
                suggestedActions=[],
                severity=GuideSeverity.INFO,
                intent=intent,
            )

        return None

    def _contains_any(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").lower().split())

    build_response = construir_respuesta


EmployeeGuideFallbackService = RespaldoGuiaFuncionario
