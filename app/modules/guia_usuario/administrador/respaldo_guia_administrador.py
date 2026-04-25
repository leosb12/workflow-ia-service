from __future__ import annotations

from dataclasses import dataclass

from app.modules.guia_usuario.comun.solicitud_guia import (
    AdminGuideRequest,
    ContextoNodoSeleccionado,
    ContextoProblemaDetectadoGuia,
    ContextoResumenPolitica,
    GuideDetectedIssueContext,
    GuideScreen,
    PantallaGuia,
    PolicySummaryContext,
    SelectedNodeContext,
    SolicitudGuiaAdministrador,
)
from app.modules.guia_usuario.comun.respuesta_guia import (
    AccionSugerida,
    AdminGuideIntent,
    AdminGuideResponse,
    CampoFormularioSugerido,
    GuideIssue,
    GuideSeverity,
    IntencionGuiaAdministrador,
    ProblemaGuia,
    RespuestaGuiaAdministrador,
    ResponsableSugerido,
    SeveridadGuia,
    SuggestedAction,
    SuggestedFormField,
    SuggestedResponsible,
)


@dataclass
class _KeywordSuggestion:
    responsible: str
    reason: str
    form: list[CampoFormularioSugerido]


class RespaldoGuiaAdministrador:
    def construir_respuesta(
        self,
        request: SolicitudGuiaAdministrador,
        intent: IntencionGuiaAdministrador,
    ) -> RespuestaGuiaAdministrador:
        issues = self._detect_issues(request.context.policy_summary, request.context.detected_issues)
        suggested_actions = self._build_suggested_actions(request, issues)
        selected_node = request.context.selected_node

        if intent == IntencionGuiaAdministrador.SUGGEST_ACTIVITY_FORM:
            form_suggestions = self._suggest_form(selected_node)
            answer = self._build_form_answer(selected_node, form_suggestions)
            return RespuestaGuiaAdministrador(
                answer=answer,
                steps=self._build_form_steps(selected_node),
                suggestedForm=form_suggestions,
                detectedIssues=issues,
                suggestedActions=suggested_actions,
                severity=SeveridadGuia.INFO,
                intent=intent,
            )

        if intent == IntencionGuiaAdministrador.SUGGEST_RESPONSIBLE:
            suggested_responsible = self._suggest_responsible(selected_node)
            answer = self._build_responsible_answer(selected_node, suggested_responsible)
            return RespuestaGuiaAdministrador(
                answer=answer,
                steps=self._build_responsible_steps(selected_node),
                suggestedResponsible=suggested_responsible,
                detectedIssues=issues,
                suggestedActions=suggested_actions,
                severity=SeveridadGuia.INFO,
                intent=intent,
            )

        if intent in {
            IntencionGuiaAdministrador.VALIDATE_POLICY,
            IntencionGuiaAdministrador.EXPLAIN_POLICY_ERROR,
            IntencionGuiaAdministrador.HELP_ACTIVATE_POLICY,
        }:
            return self._build_validation_response(request, intent, issues, suggested_actions)

        if intent in {
            IntencionGuiaAdministrador.EXPLAIN_SCREEN,
            IntencionGuiaAdministrador.WHAT_CAN_I_DO_HERE,
            IntencionGuiaAdministrador.GUIDE_STEP_BY_STEP,
            IntencionGuiaAdministrador.HELP_CREATE_POLICY,
        }:
            return self._build_screen_response(request, intent, issues, suggested_actions)

        if intent == IntencionGuiaAdministrador.SUGGEST_DECISION:
            return self._build_decision_response(request, intent, issues, suggested_actions)

        if intent == IntencionGuiaAdministrador.SUGGEST_NEXT_ACTIVITY:
            return self._build_next_activity_response(request, intent, issues, suggested_actions)

        if intent == IntencionGuiaAdministrador.OPTIMIZE_POLICY:
            return self._build_optimization_response(request, intent, issues, suggested_actions)

        return RespuestaGuiaAdministrador(
            answer=self._build_general_help_answer(request),
            steps=self._build_general_help_steps(request),
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=self._severity_from_issues(issues),
            intent=intent,
        )

    def _build_screen_response(
        self,
        request: SolicitudGuiaAdministrador,
        intent: IntencionGuiaAdministrador,
        issues: list[ProblemaGuia],
        suggested_actions: list[AccionSugerida],
    ) -> RespuestaGuiaAdministrador:
        screen = request.screen
        policy_name = request.context.policy_name or "esta politica"
        node_name = request.context.selected_node.name if request.context.selected_node else None

        if screen == PantallaGuia.POLICY_DESIGNER:
            answer = (
                f"Estas en el disenador de politicas de {policy_name}. Aqui puedes construir el flujo "
                "agregando nodos, decisiones, responsables, formularios y conexiones."
            )
            if node_name:
                answer += f" Ahora mismo tienes seleccionado el nodo {node_name}, asi que puedes revisar su responsable, formulario y conexiones."
            steps = [
                "Empieza por confirmar nodo de inicio y nodo final.",
                "Luego define las actividades principales y sus responsables.",
                "Despues agrega formularios y condiciones de decision.",
                "Finalmente conecta todo y valida la activacion.",
            ]
        elif screen == PantallaGuia.POLICY_LIST:
            answer = (
                "Estas en el modulo de politicas. Aqui puedes crear nuevas politicas, editar borradores, "
                "activar, pausar o desactivar flujos existentes."
            )
            steps = [
                "Crea una politica nueva o abre un borrador existente.",
                "Entra al disenador para completar nodos, responsables y formularios.",
                "Valida el flujo antes de activar.",
            ]
        else:
            answer = self._build_general_help_answer(request)
            steps = self._build_general_help_steps(request)

        if intent == IntencionGuiaAdministrador.GUIDE_STEP_BY_STEP:
            steps = self._build_step_by_step_flow(request)

        return RespuestaGuiaAdministrador(
            answer=answer,
            steps=steps,
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=self._severity_from_issues(issues),
            intent=intent,
        )

    def _build_validation_response(
        self,
        request: SolicitudGuiaAdministrador,
        intent: IntencionGuiaAdministrador,
        issues: list[ProblemaGuia],
        suggested_actions: list[AccionSugerida],
    ) -> RespuestaGuiaAdministrador:
        policy_name = request.context.policy_name or "la politica actual"
        if not issues:
            answer = (
                f"{policy_name} ya cumple las validaciones basicas para activarse. "
                "Te recomiendo guardar el flujo y hacer una ultima revision visual antes de activarla."
            )
            severity = SeveridadGuia.SUCCESS
            steps = [
                "Guarda el flujo para asegurar la ultima version.",
                "Revisa visualmente conexiones y decisiones.",
                "Activa la politica desde la barra superior.",
            ]
        else:
            issue_text = "; ".join(issue.message for issue in issues[:3])
            answer = (
                f"Todavia no conviene activar {policy_name}. Detecte estos bloqueos principales: {issue_text}."
            )
            severity = SeveridadGuia.ERROR
            steps = self._build_activation_steps(issues)

        return RespuestaGuiaAdministrador(
            answer=answer,
            steps=steps,
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=severity,
            intent=intent,
        )

    def _build_decision_response(
        self,
        request: AdminGuideRequest,
        intent: AdminGuideIntent,
        issues: list[GuideIssue],
        suggested_actions: list[SuggestedAction],
    ) -> AdminGuideResponse:
        node = request.context.selected_node
        answer = (
            "Para una decision conviene definir primero que campo del formulario la dispara y luego conectar "
            "claramente la salida SI y la salida NO."
        )
        if node and node.name:
            answer = (
                f"Para el nodo {node.name}, define una regla clara y mutuamente excluyente. "
                "Usa la salida derecha para SI y la izquierda para NO si tu canvas sigue esa convencion."
            )

        return AdminGuideResponse(
            answer=answer,
            steps=[
                "Identifica el campo del formulario que realmente decide el camino.",
                "Configura una condicion positiva y un camino alternativo o negativo.",
                "Verifica que ambas ramas esten conectadas a un siguiente nodo valido.",
            ],
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=self._severity_from_issues(issues),
            intent=intent,
        )

    def _build_next_activity_response(
        self,
        request: AdminGuideRequest,
        intent: AdminGuideIntent,
        issues: list[GuideIssue],
        suggested_actions: list[SuggestedAction],
    ) -> AdminGuideResponse:
        node = request.context.selected_node
        if node and self._normalize(node.name).find("revision") >= 0:
            answer = (
                f"Despues de {node.name}, normalmente conviene pasar a una decision o a una aprobacion, "
                "segun el resultado de la revision."
            )
        else:
            answer = (
                "La siguiente actividad deberia cerrar el paso actual: validar, aprobar, corregir, notificar o finalizar, "
                "segun el objetivo de la politica."
            )

        return AdminGuideResponse(
            answer=answer,
            steps=[
                "Piensa que resultado deja la actividad actual.",
                "Define si el siguiente nodo es otra actividad, una decision o el fin.",
                "Conecta el flujo y revisa si hace falta formulario o responsable.",
            ],
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=self._severity_from_issues(issues),
            intent=intent,
        )

    def _build_optimization_response(
        self,
        request: AdminGuideRequest,
        intent: AdminGuideIntent,
        issues: list[GuideIssue],
        suggested_actions: list[SuggestedAction],
    ) -> AdminGuideResponse:
        answer = (
            "Para optimizar la politica, reduce pasos sin valor, define responsables claros, evita decisiones ambiguas "
            "y agrega solo los formularios que realmente alimentan una validacion o decision."
        )
        if issues:
            answer += " Ahora mismo conviene resolver primero los bloqueos estructurales antes de optimizar detalles."

        return AdminGuideResponse(
            answer=answer,
            steps=[
                "Elimina nodos redundantes o conexiones sin salida clara.",
                "Asegura responsable y formulario en cada actividad que capture o valide datos.",
                "Convierte decisiones vagas en reglas basadas en campos concretos.",
            ],
            detectedIssues=issues,
            suggestedActions=suggested_actions,
            severity=self._severity_from_issues(issues),
            intent=intent,
        )

    def _build_general_help_answer(self, request: AdminGuideRequest) -> str:
        if request.screen == PantallaGuia.POLICY_DESIGNER:
            return (
                "Puedo ayudarte a disenar la politica, sugerir responsables, proponer formularios, validar si ya puede activarse "
                "y explicarte el siguiente paso segun el nodo o la pantalla actual."
            )
        return (
            "Puedo orientarte en el modulo admin segun la pantalla actual y, cuando estes en el disenador, "
            "tambien puedo ayudarte con responsables, formularios, decisiones y validacion de politicas."
        )

    def _build_general_help_steps(self, request: AdminGuideRequest) -> list[str]:
        if request.screen == PantallaGuia.POLICY_DESIGNER:
            return [
                "Preguntame que hacer aqui para explicarte la pantalla.",
                "Preguntame que formulario o responsable conviene para una actividad.",
                "Preguntame que falta antes de activar la politica.",
            ]
        return [
            "Abre una politica o entra al disenador para recibir ayuda contextual mas profunda.",
            "Puedes pedirme una explicacion de la pantalla o del siguiente paso.",
        ]

    def _build_step_by_step_flow(self, request: AdminGuideRequest) -> list[str]:
        if request.screen == PantallaGuia.POLICY_DESIGNER:
            return [
                "Agrega un nodo de inicio.",
                "Crea las actividades principales del tramite.",
                "Asigna responsable a cada actividad.",
                "Agrega formularios en actividades que capturan o validan datos.",
                "Conecta nodos y configura decisiones.",
                "Cierra con un nodo final y valida la activacion.",
            ]
        return [
            "Entra al modulo de politicas.",
            "Crea o abre una politica.",
            "Abre el disenador para construir el flujo.",
        ]

    def _build_form_answer(
        self,
        selected_node: SelectedNodeContext | None,
        suggestions: list[SuggestedFormField],
    ) -> str:
        if selected_node and selected_node.name:
            return (
                f"Para la actividad {selected_node.name}, te conviene un formulario corto pero util para capturar "
                "los datos que realmente disparan la siguiente decision o validacion."
            )
        return (
            "Te conviene un formulario enfocado en los datos que la actividad necesita capturar, validar o dejar como evidencia."
        )

    def _build_form_steps(self, selected_node: SelectedNodeContext | None) -> list[str]:
        steps = [
            "Agrega primero el campo principal que define el resultado de la actividad.",
            "Despues agrega observaciones o evidencia si hacen falta.",
            "Marca como obligatorios solo los datos que bloquean el avance del flujo.",
        ]
        if selected_node and selected_node.outgoing_nodes:
            steps.append(
                f"Piensa el formulario en funcion del siguiente paso: {selected_node.outgoing_nodes[0]}."
            )
        return steps[:4]

    def _build_responsible_answer(
        self,
        selected_node: SelectedNodeContext | None,
        suggestion: SuggestedResponsible | None,
    ) -> str:
        if suggestion is None:
            return (
                "Conviene asignar un responsable que tenga autoridad real para ejecutar o validar esa actividad."
            )
        if selected_node and selected_node.name:
            return (
                f"Para la actividad {selected_node.name}, conviene asignar {suggestion.name}. {suggestion.reason}"
            )
        return f"Conviene asignar {suggestion.name}. {suggestion.reason}"

    def _build_responsible_steps(self, selected_node: SelectedNodeContext | None) -> list[str]:
        steps = [
            "Valida que el responsable pueda ejecutar esa tarea sin depender de otro nodo.",
            "Si la actividad es interna, prioriza departamento o funcionario operativo.",
            "Si la actividad solo pide datos al solicitante, usa un responsable orientado al iniciador del tramite.",
        ]
        if selected_node and selected_node.department:
            steps.append(f"Como referencia, el nodo ya esta ubicado en el area {selected_node.department}.")
        return steps[:4]

    def _suggest_form(self, selected_node: SelectedNodeContext | None) -> list[SuggestedFormField]:
        if selected_node and selected_node.form_fields:
            return [
                SuggestedFormField(label=field.label, type=self._normalize_field_type(field.type), required=bool(field.required))
                for field in selected_node.form_fields[:4]
            ]

        suggestion = self._keyword_suggestion(selected_node)
        return suggestion.form if suggestion else self._default_form_suggestions()

    def _suggest_responsible(self, selected_node: SelectedNodeContext | None) -> SuggestedResponsible | None:
        if selected_node and selected_node.department:
            return SuggestedResponsible(
                name=selected_node.department,
                reason="Ese nodo ya esta ubicado en el area visual mas coherente con la actividad.",
            )

        suggestion = self._keyword_suggestion(selected_node)
        if suggestion:
            return SuggestedResponsible(name=suggestion.responsible, reason=suggestion.reason)

        return SuggestedResponsible(
            name="Departamento Operativo Responsable",
            reason="Conviene asignarlo al area que ejecuta o valida directamente la tarea.",
        )

    def _keyword_suggestion(self, selected_node: SelectedNodeContext | None) -> _KeywordSuggestion | None:
        name = self._normalize(selected_node.name if selected_node else "")

        catalog: list[tuple[list[str], _KeywordSuggestion]] = [
            (
                ["tecnica", "tecnico", "viabilidad", "inspeccion", "instalacion"],
                _KeywordSuggestion(
                    responsible="Departamento Tecnico",
                    reason="Porque la actividad requiere validacion tecnica, viabilidad o evidencia operativa.",
                    form=[
                        SuggestedFormField(label="Es viable tecnicamente?", type="BOOLEAN", required=True),
                        SuggestedFormField(label="Observaciones tecnicas", type="TEXTAREA", required=False),
                        SuggestedFormField(label="Foto o evidencia del lugar", type="FILE", required=False),
                        SuggestedFormField(label="Motivo de rechazo", type="TEXTAREA", required=False),
                    ],
                ),
            ),
            (
                ["documental", "documento", "adjunto", "archivo"],
                _KeywordSuggestion(
                    responsible="Mesa de Entrada o Control Documental",
                    reason="Porque la tarea consiste en revisar integridad documental y respaldo adjunto.",
                    form=[
                        SuggestedFormField(label="Documentacion completa?", type="BOOLEAN", required=True),
                        SuggestedFormField(label="Documentos observados", type="TEXTAREA", required=False),
                        SuggestedFormField(label="Archivo de respaldo", type="FILE", required=False),
                    ],
                ),
            ),
            (
                ["aprob", "autoriza", "valida", "revision"],
                _KeywordSuggestion(
                    responsible="Area Aprobadora",
                    reason="Porque la actividad implica revision, validacion o aprobacion formal.",
                    form=[
                        SuggestedFormField(label="Resultado de la revision", type="BOOLEAN", required=True),
                        SuggestedFormField(label="Observaciones", type="TEXTAREA", required=False),
                        SuggestedFormField(label="Fecha de revision", type="DATE", required=False),
                    ],
                ),
            ),
            (
                ["pago", "cobro", "factura", "finanza"],
                _KeywordSuggestion(
                    responsible="Finanzas",
                    reason="Porque la actividad involucra control economico, pago o validacion financiera.",
                    form=[
                        SuggestedFormField(label="Monto registrado", type="NUMBER", required=True),
                        SuggestedFormField(label="Comprobante adjunto", type="FILE", required=False),
                        SuggestedFormField(label="Observaciones financieras", type="TEXTAREA", required=False),
                    ],
                ),
            ),
            (
                ["notifica", "comunica", "avisa"],
                _KeywordSuggestion(
                    responsible="Atencion al Cliente",
                    reason="Porque la actividad esta orientada a comunicar el resultado del tramite.",
                    form=[
                        SuggestedFormField(label="Canal de notificacion", type="SELECT", required=True),
                        SuggestedFormField(label="Mensaje enviado", type="TEXTAREA", required=True),
                        SuggestedFormField(label="Fecha de notificacion", type="DATE", required=False),
                    ],
                ),
            ),
        ]

        for keywords, suggestion in catalog:
            if any(keyword in name for keyword in keywords):
                return suggestion

        return None

    def _default_form_suggestions(self) -> list[SuggestedFormField]:
        return [
            SuggestedFormField(label="Resultado de la actividad", type="BOOLEAN", required=True),
            SuggestedFormField(label="Observaciones", type="TEXTAREA", required=False),
            SuggestedFormField(label="Evidencia adjunta", type="FILE", required=False),
        ]

    def _detect_issues(
        self,
        summary: PolicySummaryContext | None,
        explicit_issues: list[GuideDetectedIssueContext],
    ) -> list[GuideIssue]:
        issues: list[GuideIssue] = [
            GuideIssue(type=item.type, message=item.message)
            for item in explicit_issues
            if item.type and item.message
        ]
        issue_types = {issue.type for issue in issues}

        if summary is None:
            return issues

        def add_issue(issue_type: str, message: str) -> None:
            if issue_type in issue_types:
                return
            issue_types.add(issue_type)
            issues.append(GuideIssue(type=issue_type, message=message))

        if not summary.has_start_node:
            add_issue("MISSING_START_NODE", "La politica no tiene nodo de inicio.")
        if not summary.has_end_node:
            add_issue("MISSING_END_NODE", "La politica no tiene nodo final.")
        if summary.activities_without_responsible > 0:
            add_issue(
                "ACTIVITIES_WITHOUT_RESPONSIBLE",
                f"Hay {summary.activities_without_responsible} actividad(es) sin responsable asignado.",
            )
        if summary.activities_without_form > 0:
            add_issue(
                "ACTIVITIES_WITHOUT_FORM",
                f"Hay {summary.activities_without_form} actividad(es) sin formulario configurado.",
            )
        if summary.invalid_connections > 0:
            add_issue(
                "INVALID_CONNECTIONS",
                f"Hay {summary.invalid_connections} conexion(es) invalidas o incompletas.",
            )
        if summary.decisions_without_routes > 0:
            add_issue(
                "DECISIONS_WITHOUT_ROUTES",
                f"Hay {summary.decisions_without_routes} decision(es) sin caminos completos.",
            )
        if summary.parallel_nodes_incomplete > 0:
            add_issue(
                "PARALLEL_FLOW_INCOMPLETE",
                f"Hay {summary.parallel_nodes_incomplete} nodo(s) de paralelismo incompletos.",
            )
        if summary.orphan_nodes > 0:
            add_issue(
                "ORPHAN_NODES",
                f"Hay {summary.orphan_nodes} nodo(s) sin conexion con el flujo principal.",
            )

        return issues

    def _build_suggested_actions(
        self,
        request: AdminGuideRequest,
        issues: list[GuideIssue],
    ) -> list[SuggestedAction]:
        actions: list[SuggestedAction] = []
        current_actions = set(request.context.available_actions)

        def add_action(action: str, label: str) -> None:
            if any(item.action == action for item in actions):
                return
            actions.append(SuggestedAction(action=action, label=label))

        issue_map = {issue.type for issue in issues}

        if "MISSING_START_NODE" in issue_map:
            add_action("ADD_START_NODE", "Agregar nodo de inicio")
        if "MISSING_END_NODE" in issue_map:
            add_action("ADD_END_NODE", "Agregar nodo final")
        if "ACTIVITIES_WITHOUT_RESPONSIBLE" in issue_map:
            add_action("ASSIGN_RESPONSIBLE", "Asignar responsables pendientes")
        if "ACTIVITIES_WITHOUT_FORM" in issue_map:
            add_action("ADD_FORM_FIELD", "Completar formularios faltantes")
        if "DECISIONS_WITHOUT_ROUTES" in issue_map or "INVALID_CONNECTIONS" in issue_map:
            add_action("CONNECT_NODES", "Corregir conexiones y decisiones")
        if request.screen == PantallaGuia.POLICY_DESIGNER and "ADD_ACTIVITY" in current_actions:
            add_action("ADD_ACTIVITY", "Agregar actividad")
        if request.screen == PantallaGuia.POLICY_DESIGNER and "SAVE_POLICY" in current_actions:
            add_action("SAVE_POLICY", "Guardar politica")
        if not issues and "ACTIVATE_POLICY" in current_actions:
            add_action("ACTIVATE_POLICY", "Activar politica")

        return actions[:5]

    def _build_activation_steps(self, issues: list[GuideIssue]) -> list[str]:
        steps: list[str] = []
        issue_types = [issue.type for issue in issues]
        if "MISSING_START_NODE" in issue_types:
            steps.append("Agrega un nodo de inicio.")
        if "MISSING_END_NODE" in issue_types:
            steps.append("Agrega un nodo final.")
        if "ACTIVITIES_WITHOUT_RESPONSIBLE" in issue_types:
            steps.append("Asigna responsable a todas las actividades.")
        if "ACTIVITIES_WITHOUT_FORM" in issue_types:
            steps.append("Completa los formularios de las actividades que capturan o validan datos.")
        if "DECISIONS_WITHOUT_ROUTES" in issue_types or "INVALID_CONNECTIONS" in issue_types:
            steps.append("Corrige las conexiones y asegura dos caminos validos en cada decision.")
        if not steps:
            steps.append("Revisa la estructura general del flujo y guarda nuevamente la politica.")
        return steps[:5]

    def _severity_from_issues(self, issues: list[GuideIssue]) -> GuideSeverity:
        if not issues:
            return GuideSeverity.INFO
        if any(issue.type.startswith("MISSING_") for issue in issues):
            return GuideSeverity.ERROR
        return GuideSeverity.WARNING

    def _normalize_field_type(self, value: str | None) -> str:
        normalized = self._normalize(value or "")
        mapping = {
            "texto": "TEXT",
            "textarea": "TEXTAREA",
            "boolean": "BOOLEAN",
            "booleano": "BOOLEAN",
            "numero": "NUMBER",
            "fecha": "DATE",
            "archivo": "FILE",
            "file": "FILE",
        }
        return mapping.get(normalized, (value or "TEXT").upper())

    def _normalize(self, value: str | None) -> str:
        return " ".join((value or "").lower().split())

    build_response = construir_respuesta


AdminGuideFallbackService = RespaldoGuiaAdministrador
