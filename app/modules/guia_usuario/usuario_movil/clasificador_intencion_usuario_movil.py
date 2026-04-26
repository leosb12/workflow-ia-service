import unicodedata

from app.modules.guia_usuario.comun.solicitud_guia import PantallaGuia
from app.modules.guia_usuario.comun.respuesta_guia import IntencionGuiaUsuarioMovil


class ClasificadorIntencionUsuarioMovil:
    def clasificar_intencion(
        self,
        pregunta: str,
        pantalla: PantallaGuia,
    ) -> IntencionGuiaUsuarioMovil:
        normalizada = self._normalize(pregunta)

        if self._contains_any(
            normalizada,
            [
                "que hago aqui",
                "donde estoy",
                "explica esta pantalla",
                "para que sirve esta pantalla",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_PANTALLA

        if self._contains_any(
            normalizada,
            [
                "que puedo hacer aqui",
                "que puedo hacer",
                "que opciones tengo",
                "que acciones tengo",
            ],
        ):
            return IntencionGuiaUsuarioMovil.QUE_PUEDO_HACER_AQUI

        if self._contains_any(
            normalizada,
            [
                "como inicio un tramite",
                "como inicio",
                "como iniciar",
                "quiero iniciar un tramite",
                "nuevo tramite",
                "iniciar tramite",
            ],
        ):
            return IntencionGuiaUsuarioMovil.AYUDA_INICIAR_TRAMITE

        if self._contains_any(
            normalizada,
            [
                "subir documento",
                "adjuntar documento",
                "cargar documento",
                "enviar documento",
            ],
        ):
            return IntencionGuiaUsuarioMovil.AYUDA_SUBIR_DOCUMENTO

        if self._contains_any(
            normalizada,
            [
                "por que fue rechazado",
                "por que lo rechazaron",
                "rechazado",
                "rechazada",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_RECHAZO

        if self._contains_any(
            normalizada,
            [
                "que documentos me faltan",
                "documentos faltantes",
                "que documento falta",
                "me falta documento",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_DOCUMENTOS_FALTANTES

        if self._contains_any(
            normalizada,
            [
                "observado",
                "observada",
                "observaciones",
                "que puedo hacer si fue observado",
                "que significa esta observacion",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_OBSERVACIONES

        if self._contains_any(
            normalizada,
            [
                "historial",
                "que ya paso",
                "que etapas ya pasaron",
                "explica el historial",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_HISTORIAL

        if self._contains_any(
            normalizada,
            [
                "que pasa despues",
                "que sigue despues",
                "proximo paso",
                "luego que sigue",
                "cuanto podria tardar",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_PROXIMO_PASO

        if self._contains_any(
            normalizada,
            [
                "en que etapa va",
                "en que etapa esta",
                "etapa actual",
                "quien lo esta revisando",
                "que area lo esta revisando",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_ETAPA_ACTUAL

        if self._contains_any(
            normalizada,
            [
                "progreso del tramite",
                "como va mi tramite",
                "que falta para que avance",
                "ya termino mi tramite",
                "ya termino",
                "avance del tramite",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_PROGRESO_TRAMITE

        if self._contains_any(
            normalizada,
            [
                "en que estado esta mi tramite",
                "en que estado esta",
                "que significa este estado",
                "por que esta detenido",
                "estado del tramite",
                "esta aprobado",
                "esta en proceso",
            ],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_ESTADO_TRAMITE

        if self._contains_any(
            normalizada,
            [
                "paso a paso",
                "guiame",
                "como hago esto",
                "como empiezo",
            ],
        ):
            return IntencionGuiaUsuarioMovil.GUIA_PASO_A_PASO

        if pantalla in {
            PantallaGuia.DETALLE_TRAMITE,
            PantallaGuia.ESTADO_TRAMITE,
        } and self._contains_any(normalizada, ["tramite", "estado", "etapa"]):
            return IntencionGuiaUsuarioMovil.EXPLICAR_ESTADO_TRAMITE

        if pantalla == PantallaGuia.LISTA_TRAMITES and self._contains_any(
            normalizada,
            ["tramite", "lista", "estado"],
        ):
            return IntencionGuiaUsuarioMovil.EXPLICAR_PANTALLA

        return IntencionGuiaUsuarioMovil.AYUDA_GENERAL_USUARIO_MOVIL

    def _contains_any(self, text: str, options: list[str]) -> bool:
        return any(option in text for option in options)

    def _normalize(self, text: str) -> str:
        normalized = unicodedata.normalize("NFD", (text or "").lower())
        without_accents = "".join(ch for ch in normalized if unicodedata.category(ch) != "Mn")
        return " ".join(without_accents.split())

    detect = clasificar_intencion


MobileUserGuideIntentClassifier = ClasificadorIntencionUsuarioMovil
