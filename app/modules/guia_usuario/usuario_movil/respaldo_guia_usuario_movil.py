from __future__ import annotations

from app.modules.guia_usuario.comun.solicitud_guia import (
    ContextoGuiaUsuarioMovil,
    ContextoResumenProgresoGuiaUsuarioMovil,
    PantallaGuia,
    SolicitudGuiaUsuarioMovil,
)
from app.modules.guia_usuario.comun.respuesta_guia import (
    AccionSugerida,
    IntencionGuiaUsuarioMovil,
    RespuestaGuiaUsuarioMovil,
    SeveridadGuia,
)


class RespaldoGuiaUsuarioMovil:
    def construir_respuesta(
        self,
        request: SolicitudGuiaUsuarioMovil,
        intent: IntencionGuiaUsuarioMovil,
    ) -> RespuestaGuiaUsuarioMovil:
        contexto = request.contexto
        acciones_sugeridas = self._build_suggested_actions(contexto)
        estado_explicado = self._build_status_explanation(contexto.estado_tramite)
        progreso_explicado = self._build_progress_explanation(contexto.resumen_progreso)
        documentos_faltantes = self._clean_text_list(contexto.documentos_faltantes)
        proximos_pasos = self._clean_text_list(contexto.proximos_pasos)
        severidad = self._severity_from_context(contexto)

        if intent in {
            IntencionGuiaUsuarioMovil.EXPLICAR_PANTALLA,
            IntencionGuiaUsuarioMovil.QUE_PUEDO_HACER_AQUI,
            IntencionGuiaUsuarioMovil.GUIA_PASO_A_PASO,
        }:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_screen_answer(request),
                pasos=self._build_screen_steps(request, intent),
                estado_explicado=estado_explicado,
                progreso_explicado=progreso_explicado,
                documentos_faltantes=documentos_faltantes,
                proximos_pasos=proximos_pasos,
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=severidad,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.AYUDA_INICIAR_TRAMITE:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_start_answer(contexto),
                pasos=self._build_start_steps(contexto),
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=SeveridadGuia.INFO,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.AYUDA_SUBIR_DOCUMENTO:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_upload_answer(contexto),
                pasos=self._build_upload_steps(contexto),
                documentos_faltantes=documentos_faltantes,
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=SeveridadGuia.WARNING if documentos_faltantes else SeveridadGuia.INFO,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_ESTADO_TRAMITE:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_status_answer(contexto),
                pasos=self._build_status_steps(contexto),
                estado_explicado=estado_explicado,
                progreso_explicado=progreso_explicado,
                documentos_faltantes=documentos_faltantes[:3],
                proximos_pasos=proximos_pasos[:3],
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=severidad,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_PROGRESO_TRAMITE:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_progress_answer(contexto),
                pasos=self._build_progress_steps(contexto),
                estado_explicado=estado_explicado,
                progreso_explicado=progreso_explicado,
                proximos_pasos=proximos_pasos[:3],
                acciones_sugeridas=acciones_sugeridas[:2],
                severidad=severidad,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_ETAPA_ACTUAL:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_stage_answer(contexto),
                pasos=self._build_stage_steps(contexto),
                estado_explicado=estado_explicado,
                proximos_pasos=proximos_pasos[:3],
                acciones_sugeridas=acciones_sugeridas[:2],
                severidad=severidad,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_HISTORIAL:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_history_answer(contexto),
                pasos=self._build_history_steps(contexto),
                progreso_explicado=progreso_explicado,
                acciones_sugeridas=acciones_sugeridas[:2],
                severidad=SeveridadGuia.INFO,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_DOCUMENTOS_FALTANTES:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_missing_documents_answer(contexto),
                pasos=self._build_missing_documents_steps(contexto),
                documentos_faltantes=documentos_faltantes,
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=SeveridadGuia.WARNING if documentos_faltantes else SeveridadGuia.INFO,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_OBSERVACIONES:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_observations_answer(contexto),
                pasos=self._build_observations_steps(contexto),
                documentos_faltantes=documentos_faltantes[:3],
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=SeveridadGuia.WARNING if contexto.observaciones else SeveridadGuia.INFO,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_RECHAZO:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_rejection_answer(contexto),
                pasos=self._build_rejection_steps(contexto),
                estado_explicado=estado_explicado,
                documentos_faltantes=documentos_faltantes,
                acciones_sugeridas=acciones_sugeridas[:3],
                severidad=SeveridadGuia.ERROR,
                intencion=intent,
            )

        if intent == IntencionGuiaUsuarioMovil.EXPLICAR_PROXIMO_PASO:
            return RespuestaGuiaUsuarioMovil(
                respuesta=self._build_next_step_answer(contexto),
                pasos=self._build_next_step_steps(contexto),
                progreso_explicado=progreso_explicado,
                proximos_pasos=proximos_pasos,
                acciones_sugeridas=acciones_sugeridas[:2],
                severidad=SeveridadGuia.INFO,
                intencion=intent,
            )

        return RespuestaGuiaUsuarioMovil(
            respuesta=self._build_general_help_answer(request),
            pasos=self._build_general_help_steps(request),
            estado_explicado=estado_explicado,
            progreso_explicado=progreso_explicado,
            documentos_faltantes=documentos_faltantes[:3],
            proximos_pasos=proximos_pasos[:3],
            acciones_sugeridas=acciones_sugeridas[:3],
            severidad=severidad,
            intencion=intent,
        )

    def _build_screen_answer(self, request: SolicitudGuiaUsuarioMovil) -> str:
        pantalla = request.pantalla
        if pantalla == PantallaGuia.INICIO_USUARIO:
            return (
                "Estas en el inicio del usuario movil. Aqui puedes ver accesos rapidos para iniciar "
                "tramites, revisar tus solicitudes y consultar notificaciones."
            )
        if pantalla == PantallaGuia.LISTA_TRAMITES:
            return (
                "Estas en la lista de tramites. Aqui puedes revisar tus solicitudes, entrar al detalle "
                "de cada una y consultar su estado."
            )
        if pantalla in {PantallaGuia.DETALLE_TRAMITE, PantallaGuia.ESTADO_TRAMITE}:
            nombre = request.contexto.nombre_politica or "tu tramite"
            return (
                f"Estas viendo el detalle de {nombre}. Aqui puedes entender el estado actual, "
                "la etapa en curso, lo que falta y los siguientes pasos."
            )
        if pantalla == PantallaGuia.FORMULARIO_SOLICITUD:
            return (
                "Estas en un formulario de solicitud. Aqui debes completar la informacion requerida "
                "y adjuntar documentos si el sistema lo pide."
            )
        if pantalla == PantallaGuia.PERFIL_USUARIO:
            return (
                "Estas en tu perfil. Aqui puedes revisar tus datos basicos y entender como se usan "
                "dentro de tus tramites."
            )
        if pantalla == PantallaGuia.NOTIFICACIONES:
            return (
                "Estas en notificaciones. Aqui puedes revisar avisos sobre avances, observaciones o "
                "cambios en tus tramites."
            )
        return (
            "Puedo ayudarte a entender la pantalla actual, revisar el estado de tu tramite y explicarte "
            "que falta para avanzar."
        )

    def _build_screen_steps(
        self,
        request: SolicitudGuiaUsuarioMovil,
        intent: IntencionGuiaUsuarioMovil,
    ) -> list[str]:
        if request.pantalla == PantallaGuia.INICIO_USUARIO:
            steps = [
                "Revisa si tienes accesos para iniciar un tramite.",
                "Entra a tu lista de tramites para consultar solicitudes ya creadas.",
                "Abre notificaciones si recibiste una alerta reciente.",
            ]
            return steps if intent == IntencionGuiaUsuarioMovil.GUIA_PASO_A_PASO else steps[:2]

        if request.pantalla == PantallaGuia.LISTA_TRAMITES:
            return [
                "Busca el tramite que quieres revisar.",
                "Abre el detalle para ver estado, etapa e historial.",
                "Si hay observaciones, revisa que te falta para avanzar.",
            ]

        if request.pantalla in {PantallaGuia.DETALLE_TRAMITE, PantallaGuia.ESTADO_TRAMITE}:
            return [
                "Revisa el estado actual del tramite.",
                "Ubica la etapa en la que esta tu solicitud.",
                "Confirma si tienes documentos u observaciones pendientes.",
            ]

        if request.pantalla == PantallaGuia.FORMULARIO_SOLICITUD:
            return [
                "Completa primero la informacion obligatoria.",
                "Adjunta documentos solo si el sistema los solicita.",
                "Revisa la solicitud antes de enviarla.",
            ]

        return [
            "Revisa la informacion principal de esta pantalla.",
            "Consulta que acciones tienes disponibles.",
            "Pregunta por el estado o el siguiente paso si necesitas mas detalle.",
        ]

    def _build_start_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if "INICIAR_TRAMITE" in contexto.acciones_disponibles:
            return (
                "Si el sistema lo permite, puedes iniciar el tramite desde esta pantalla y luego seguir "
                "su avance desde tu lista de solicitudes."
            )
        return (
            "Para iniciar un tramite, primero debes entrar a la seccion donde el sistema muestre tramites "
            "disponibles para ti."
        )

    def _build_start_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Busca el tramite que quieres iniciar.",
            "Completa la solicitud con la informacion requerida.",
            "Despues revisa su estado desde tu lista de tramites.",
        ]
        if "INICIAR_TRAMITE" not in contexto.acciones_disponibles:
            steps[0] = "Verifica primero si esta pantalla permite iniciar tramites."
        return steps

    def _build_upload_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.documentos_faltantes:
            documentos = ", ".join(contexto.documentos_faltantes[:3])
            return (
                f"Para que tu tramite avance, todavia faltan estos documentos: {documentos}. "
                "Subelos desde la accion disponible del tramite si el sistema te lo permite."
            )
        return (
            "Si debes subir un documento, usa la accion disponible del tramite y revisa que el archivo "
            "corresponda exactamente a lo solicitado."
        )

    def _build_upload_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Revisa que documento te estan pidiendo.",
            "Sube el archivo desde la opcion del tramite.",
            "Confirma despues si la observacion o el bloqueo desaparecio.",
        ]
        if not contexto.documentos_faltantes:
            steps[0] = "Verifica primero si realmente tienes documentos pendientes."
        return steps

    def _build_status_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        etapa = contexto.etapa_actual.nombre if contexto.etapa_actual else None
        estado = contexto.estado_tramite or "SIN_ESTADO"
        if etapa:
            return f"Tu tramite esta en {etapa}. {self._build_status_explanation(estado)}"
        return f"El estado actual de tu tramite es {estado}. {self._build_status_explanation(estado)}"

    def _build_status_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Revisa si tienes observaciones o documentos pendientes.",
            "Confirma en que etapa se encuentra la solicitud.",
            "Consulta que paso sigue despues de la revision actual.",
        ]
        if contexto.estado_tramite and self._normalize_code(contexto.estado_tramite) in {"RECHAZADO", "CANCELADO"}:
            steps[0] = "Lee el motivo del rechazo o cancelacion."
        return steps

    def _build_progress_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.resumen_progreso and contexto.resumen_progreso.paso_actual:
            return (
                f"Tu solicitud va por {contexto.resumen_progreso.paso_actual}. "
                f"{self._build_progress_explanation(contexto.resumen_progreso)}"
            )
        return "Puedo explicarte que etapas ya pasaron, en cual estas ahora y que falta para terminar."

    def _build_progress_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Revisa la etapa actual del tramite.",
            "Confirma cuantos pasos ya se completaron.",
            "Consulta los proximos pasos para saber que falta.",
        ]
        if contexto.historial:
            steps.append("Si quieres mas detalle, revisa tambien el historial reciente.")
        return steps[:4]

    def _build_stage_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        etapa = contexto.etapa_actual
        if etapa and etapa.nombre:
            base = f"Tu solicitud esta en la etapa {etapa.nombre}."
            if etapa.descripcion:
                base += f" {etapa.descripcion}"
            if etapa.departamento:
                base += f" Ahora la esta revisando el area {etapa.departamento}."
            elif etapa.responsable:
                base += f" Ahora la esta revisando {etapa.responsable}."
            return base
        return "No tengo una etapa actual detallada, pero puedo orientarte con el estado general del tramite."

    def _build_stage_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Ubica la etapa actual del tramite.",
            "Revisa si esa etapa depende de un documento o correccion pendiente.",
            "Consulta el siguiente paso para saber que vendra despues.",
        ]
        if contexto.etapa_actual and contexto.etapa_actual.departamento:
            steps.append(f"El area actual es {contexto.etapa_actual.departamento}.")
        return steps[:4]

    def _build_history_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.historial:
            ultimo = contexto.historial[-1]
            etapa = ultimo.etapa or "una etapa previa"
            estado = ultimo.estado or "SIN_ESTADO"
            fecha = ultimo.fecha or "sin fecha registrada"
            return (
                f"En tu historial, el ultimo avance registrado fue {etapa} con estado {estado} "
                f"en fecha {fecha}."
            )
        return "Todavia no tengo eventos de historial suficientes para mostrarte avances previos del tramite."

    def _build_history_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Revisa que etapa ya fue completada.",
            "Identifica el ultimo cambio registrado.",
            "Compara ese avance con la etapa actual del tramite.",
        ]
        if contexto.historial:
            steps.append(f"Hay {len(contexto.historial)} registro(s) en el historial disponible.")
        return steps[:4]

    def _build_missing_documents_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.documentos_faltantes:
            documentos = ", ".join(contexto.documentos_faltantes[:4])
            return f"Los documentos pendientes por ahora son: {documentos}."
        return "Por ahora no veo documentos faltantes informados en el contexto disponible."

    def _build_missing_documents_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        if contexto.documentos_faltantes:
            return [
                "Revisa cada documento solicitado.",
                "Sube o corrige solo los documentos faltantes.",
                "Vuelve a consultar el estado despues del envio.",
            ]
        return [
            "Si esperabas un documento pendiente, revisa observaciones del tramite.",
            "Tambien puedes consultar el detalle para confirmar si hubo una actualizacion reciente.",
        ]

    def _build_observations_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.observaciones:
            observacion = contexto.observaciones[0]
            return f"Tu tramite tiene observaciones pendientes. La principal es: {observacion}"
        return "No veo observaciones registradas en el contexto actual del tramite."

    def _build_observations_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        if contexto.observaciones:
            return [
                "Lee con cuidado la observacion registrada.",
                "Corrige o adjunta lo que te pidieron.",
                "Despues vuelve a consultar si el tramite pudo continuar.",
            ]
        return [
            "Si el tramite sigue detenido, revisa el estado y el historial reciente.",
            "Tambien puedes consultar si faltan documentos para avanzar.",
        ]

    def _build_rejection_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.observaciones:
            return (
                "Tu tramite fue rechazado o detenido por una observacion registrada. "
                f"El motivo disponible es: {contexto.observaciones[0]}"
            )
        return (
            "Tu tramite aparece como rechazado o cerrado negativamente. Si no ves un motivo exacto, "
            "revisa el historial y las observaciones mas recientes."
        )

    def _build_rejection_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Revisa el motivo del rechazo u observacion.",
            "Confirma si puedes corregir documentos o datos.",
            "Si el sistema lo permite, vuelve a enviar o iniciar una nueva solicitud.",
        ]
        if not contexto.documentos_faltantes:
            return steps[:2]
        return steps

    def _build_next_step_answer(self, contexto: ContextoGuiaUsuarioMovil) -> str:
        if contexto.proximos_pasos:
            siguiente = contexto.proximos_pasos[0]
            return f"El siguiente paso esperado de tu tramite es {siguiente}."
        return "Todavia no tengo un siguiente paso detallado, pero puedo orientarte con el estado y la etapa actual."

    def _build_next_step_steps(self, contexto: ContextoGuiaUsuarioMovil) -> list[str]:
        steps = [
            "Confirma si la etapa actual ya puede cerrarse.",
            "Revisa si queda alguna observacion o documento pendiente.",
            "Despues consulta el proximo paso del flujo.",
        ]
        if contexto.proximos_pasos:
            steps[2] = f"El siguiente paso informado es {contexto.proximos_pasos[0]}."
        return steps

    def _build_general_help_answer(self, request: SolicitudGuiaUsuarioMovil) -> str:
        if request.pantalla in {PantallaGuia.DETALLE_TRAMITE, PantallaGuia.ESTADO_TRAMITE}:
            return (
                "Puedo explicarte en que estado va tu tramite, en que etapa esta, que falta para avanzar "
                "y que pasara despues."
            )
        if request.pantalla == PantallaGuia.LISTA_TRAMITES:
            return (
                "Puedo ayudarte a entender tu lista de tramites, explicarte estados y decirte que hacer "
                "cuando una solicitud este observada o detenida."
            )
        return (
            "Puedo ayudarte a entender la pantalla actual, iniciar tramites si el sistema lo permite y "
            "explicarte el estado de tus solicitudes."
        )

    def _build_general_help_steps(self, request: SolicitudGuiaUsuarioMovil) -> list[str]:
        if request.pantalla == PantallaGuia.LISTA_TRAMITES:
            return [
                "Preguntame que puedes hacer aqui.",
                "Preguntame en que estado va un tramite.",
                "Preguntame que falta para que una solicitud avance.",
            ]
        if request.pantalla in {PantallaGuia.DETALLE_TRAMITE, PantallaGuia.ESTADO_TRAMITE}:
            return [
                "Preguntame que significa el estado actual.",
                "Preguntame en que etapa va tu solicitud.",
                "Preguntame que pasa despues o que documento falta.",
            ]
        return [
            "Preguntame que puedes hacer en esta pantalla.",
            "Preguntame como iniciar un tramite o como revisar uno ya creado.",
        ]

    def _build_status_explanation(self, estado: str | None) -> str | None:
        normalized = self._normalize_code(estado)
        mapping = {
            "EN_PROCESO": "EN_PROCESO significa que tu tramite todavia esta siendo revisado.",
            "EN_CURSO": "EN_CURSO significa que tu tramite todavia esta avanzando dentro del flujo.",
            "DETENIDO": "DETENIDO significa que el tramite no puede avanzar por ahora.",
            "PAUSADO": "PAUSADO significa que el tramite quedo temporalmente en espera.",
            "OBSERVADO": "OBSERVADO significa que encontraron algo por corregir o completar.",
            "RECHAZADO": "RECHAZADO significa que la solicitud no pudo continuar con la informacion actual.",
            "APROBADO": "APROBADO significa que la solicitud fue aceptada.",
            "FINALIZADO": "FINALIZADO significa que el tramite ya termino.",
            "FINALIZADA": "FINALIZADA significa que el tramite ya termino.",
            "CANCELADO": "CANCELADO significa que el tramite se cerro sin continuar.",
        }
        return mapping.get(normalized, f"El estado actual informado es {estado}." if estado else None)

    def _build_progress_explanation(
        self,
        resumen: ContextoResumenProgresoGuiaUsuarioMovil | None,
    ) -> str | None:
        if resumen is None:
            return None
        total = max(resumen.pasos_completados + resumen.pasos_pendientes, 0)
        parts: list[str] = []
        if total > 0:
            parts.append(f"Llevas {resumen.pasos_completados} de {total} etapas completadas.")
        if resumen.paso_actual:
            parts.append(f"La etapa actual es {resumen.paso_actual}.")
        if resumen.porcentaje_avance:
            parts.append(f"El avance estimado es {resumen.porcentaje_avance}%.")
        return " ".join(parts) or None

    def _build_suggested_actions(
        self,
        contexto: ContextoGuiaUsuarioMovil,
    ) -> list[AccionSugerida]:
        labels = {
            "INICIAR_TRAMITE": "Iniciar tramite",
            "CONSULTAR_ESTADO": "Consultar estado del tramite",
            "VER_HISTORIAL": "Ver historial del tramite",
            "VER_OBSERVACIONES": "Ver observaciones",
            "SUBIR_DOCUMENTO": "Subir documento pendiente",
            "VER_DETALLE_TRAMITE": "Ver detalle del tramite",
            "VER_NOTIFICACIONES": "Ver notificaciones",
            "ACTUALIZAR_PERFIL": "Actualizar perfil",
        }
        priority = [
            "SUBIR_DOCUMENTO",
            "VER_OBSERVACIONES",
            "CONSULTAR_ESTADO",
            "VER_HISTORIAL",
            "VER_DETALLE_TRAMITE",
            "INICIAR_TRAMITE",
            "VER_NOTIFICACIONES",
            "ACTUALIZAR_PERFIL",
        ]
        available = {self._normalize_code(action): action for action in contexto.acciones_disponibles}
        actions: list[AccionSugerida] = []
        for code in priority:
            if code not in available:
                continue
            actions.append(AccionSugerida(action=code, label=labels.get(code, code.replace("_", " ").title())))
        return actions[:5]

    def _severity_from_context(self, contexto: ContextoGuiaUsuarioMovil) -> SeveridadGuia:
        estado = self._normalize_code(contexto.estado_tramite)
        if estado in {"RECHAZADO", "CANCELADO"}:
            return SeveridadGuia.ERROR
        if contexto.documentos_faltantes or contexto.observaciones or estado in {"DETENIDO", "PAUSADO", "OBSERVADO"}:
            return SeveridadGuia.WARNING
        if estado in {"APROBADO", "FINALIZADO", "FINALIZADA"}:
            return SeveridadGuia.SUCCESS
        return SeveridadGuia.INFO

    def _clean_text_list(self, values: list[str]) -> list[str]:
        cleaned: list[str] = []
        for value in values[:5]:
            text = " ".join((value or "").split())
            if text:
                cleaned.append(text[:300])
        return cleaned

    def _normalize_code(self, value: str | None) -> str:
        if not isinstance(value, str):
            return ""
        return value.strip().upper()

    build_response = construir_respuesta


MobileUserGuideFallbackService = RespaldoGuiaUsuarioMovil
