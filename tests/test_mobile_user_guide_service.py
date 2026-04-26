import asyncio

from app.modules.user_guide.prompts.mobile_user_guide_prompts import MobileUserGuidePrompts
from app.modules.user_guide.schemas.guide_request import MobileUserGuideRequest
from app.modules.user_guide.service.mobile_user_guide_fallback_service import (
    MobileUserGuideFallbackService,
)
from app.modules.user_guide.service.mobile_user_guide_intent_classifier import (
    MobileUserGuideIntentClassifier,
)
from app.modules.user_guide.service.mobile_user_guide_service import MobileUserGuideService
from app.shared.llm.json_parser import JsonObjectParser


class FailingPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        raise RuntimeError("LLM unavailable")


class StubPromptRunner:
    async def run_json_prompt(self, **kwargs) -> str:
        return """
        {
          "answer": "Tu tramite esta en Evaluacion tecnica. El area tecnica revisa si puede continuar.",
          "steps": ["Revisa si tienes observaciones pendientes", "Espera la validacion tecnica"],
          "estadoExplicado": "EN_PROCESO significa que tu tramite todavia esta siendo revisado.",
          "progresoExplicado": "Llevas 2 de 5 etapas completadas.",
          "documentosFaltantes": ["Croquis del domicilio"],
          "proximosPasos": ["Revision legal", "Asignacion de almacen"],
          "accionesSugeridas": [
            {"action": "VER_HISTORIAL", "label": "Ver historial del tramite"}
          ],
          "severity": "WARNING",
          "intent": "EXPLICAR_ESTADO_TRAMITE",
          "source": "AI",
          "available": true
        }
        """


def build_request(question: str) -> MobileUserGuideRequest:
    return MobileUserGuideRequest.model_validate(
        {
            "userId": "usr-1",
            "userName": "Usuario Movil",
            "role": "MOBILE_USER",
            "screen": "DETALLE_TRAMITE",
            "question": question,
            "context": {
                "tramiteId": "inst-1",
                "politicaId": "pol-1",
                "nombrePolitica": "Instalacion de medidor",
                "estadoTramite": "EN_PROCESO",
                "etapaActual": {
                    "id": "node-1",
                    "nombre": "Evaluacion tecnica",
                    "descripcion": "El area tecnica revisa la viabilidad de la solicitud",
                    "departamento": "Departamento Tecnico",
                },
                "resumenProgreso": {
                    "pasosCompletados": 2,
                    "pasoActual": "Evaluacion tecnica",
                    "pasosPendientes": 3,
                    "porcentajeAvance": 40,
                },
                "historial": [
                    {
                        "etapa": "Recepcion de solicitud",
                        "estado": "COMPLETADO",
                        "fecha": "2026-04-25",
                    }
                ],
                "documentosFaltantes": ["Croquis del domicilio"],
                "observaciones": ["Falta respaldar la ubicacion exacta."],
                "proximosPasos": ["Revision legal", "Asignacion de almacen"],
                "accionesDisponibles": [
                    "CONSULTAR_ESTADO",
                    "VER_HISTORIAL",
                    "VER_OBSERVACIONES",
                    "SUBIR_DOCUMENTO",
                ],
            },
        }
    )


def test_mobile_user_guide_uses_fallback_when_llm_fails() -> None:
    service = MobileUserGuideService(
        prompt_runner=FailingPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=MobileUserGuidePrompts(),
        classifier=MobileUserGuideIntentClassifier(),
        fallback_service=MobileUserGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_mobile_user(build_request("Que documentos me faltan?")))

    assert response.disponible is True
    assert response.fuente == "HEURISTIC"
    assert response.documentos_faltantes
    assert response.documentos_faltantes[0] == "Croquis del domicilio"


def test_mobile_user_guide_sanitizes_ai_response() -> None:
    service = MobileUserGuideService(
        prompt_runner=StubPromptRunner(),
        json_parser=JsonObjectParser(),
        prompts=MobileUserGuidePrompts(),
        classifier=MobileUserGuideIntentClassifier(),
        fallback_service=MobileUserGuideFallbackService(),
        llm_model="deepseek-v4-flash",
    )

    response = asyncio.run(service.guide_mobile_user(build_request("En que estado esta mi tramite?")))

    assert response.fuente == "AI"
    assert response.intencion == "EXPLICAR_ESTADO_TRAMITE"
    assert response.estado_explicado is not None
    assert response.documentos_faltantes
    assert response.acciones_sugeridas[0].action == "VER_HISTORIAL"
