import logging
from typing import Any

from pydantic import ValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_502_BAD_GATEWAY

from app.core.exceptions import ApiException
from app.modules.workflow_generator.domain.models import WorkflowJsonValidator
from app.modules.workflow_generator.domain.prompts import WorkflowPrompts
from app.modules.workflow_generator.schemas import (
    GenerationContext,
    TextoAFlujoRequest,
    TextoAFlujoResponse,
)
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.prompt_runner import PromptRunner

log = logging.getLogger(__name__)


class GenerateWorkflowUseCase:
    MAX_INTENTOS_IA = 3

    def __init__(
        self,
        prompt_runner: PromptRunner,
        workflow_validator: WorkflowJsonValidator,
        json_parser: JsonObjectParser,
        prompts: WorkflowPrompts,
    ) -> None:
        self.prompt_runner = prompt_runner
        self.workflow_validator = workflow_validator
        self.json_parser = json_parser
        self.prompts = prompts

    async def execute(self, request: TextoAFlujoRequest) -> TextoAFlujoResponse:
        descripcion = self._validar_descripcion(request)
        context = request.context

        try:
            workflow = await self._generar_workflow_con_reintentos(descripcion, context)
        except Exception as exc:
            log.warning(
                "Fallo la generacion de DeepSeek, se devolvera workflow fallback: %s",
                exc,
            )
            workflow = self._construir_workflow_fallback(descripcion)

        try:
            self.workflow_validator.validate(workflow)
        except Exception as exc:
            log.warning("El workflow generado no paso validacion: %s", exc)
            raise ApiException(
                HTTP_400_BAD_REQUEST,
                "Workflow IA invalido: no cumple las reglas del validador",
            ) from exc

        try:
            response = TextoAFlujoResponse.model_validate(workflow)
        except ValidationError as exc:
            log.warning("Workflow IA no coincide con el DTO de respuesta: %s", exc)
            raise ApiException(
                HTTP_400_BAD_REQUEST,
                "Workflow IA invalido: la estructura no coincide con el contrato de respuesta",
            ) from exc

        log.info(
            "Workflow generado correctamente. nodos=%s transiciones=%s formularios=%s",
            len(response.nodes),
            len(response.transitions),
            len(response.forms),
        )
        return response

    async def _generar_workflow_con_reintentos(
        self,
        descripcion: str,
        context: GenerationContext | None,
    ) -> dict[str, Any]:
        system_prompt = self.prompts.construir_system_prompt()
        user_prompt = self.prompts.construir_user_prompt(descripcion, context)

        ultimo_error: Exception | None = None
        ultimo_raw: str = ""

        for intento in range(1, self.MAX_INTENTOS_IA + 1):
            raw_json = ""
            try:
                raw_json = await self.prompt_runner.run_json_prompt(
                    system_prompt=system_prompt,
                    user_prompt=user_prompt,
                )
                workflow = self.json_parser.parse(raw_json)
                self.workflow_validator.validate(workflow)
                return workflow
            except Exception as exc:
                ultimo_error = exc
                if raw_json:
                    ultimo_raw = raw_json

                log.warning(
                    "Intento IA %s/%s fallido: %s",
                    intento,
                    self.MAX_INTENTOS_IA,
                    exc,
                )

                if intento < self.MAX_INTENTOS_IA:
                    user_prompt = self.prompts.construir_prompt_reintento(
                        descripcion=descripcion,
                        context=context,
                        raw_prev=ultimo_raw,
                        error=str(exc),
                        intento=intento + 1,
                    )

        if ultimo_error is not None:
            raise ultimo_error

        raise ApiException(
            HTTP_502_BAD_GATEWAY,
            "No fue posible generar el workflow con IA",
        )

    def _validar_descripcion(self, request: TextoAFlujoRequest) -> str:
        descripcion = request.descripcion.strip()
        if not descripcion:
            raise ApiException(
                HTTP_400_BAD_REQUEST,
                "La descripcion es obligatoria",
            )
        return descripcion

    def _construir_workflow_fallback(self, descripcion: str) -> dict[str, Any]:
        objetivo = descripcion.strip()[:220] or "Procesar solicitud"

        return {
            "policy": {
                "name": "workflow_fallback",
                "description": "Workflow generado por contingencia",
                "objective": objetivo,
                "version": "1.0",
            },
            "departments": [
                {
                    "id": "administracion",
                    "name": "Administracion",
                    "description": "Departamento generico de contingencia",
                    "aliases": ["administraciÃ³n"],
                }
            ],
            "roles": [
                {
                    "id": "operador",
                    "name": "Operador",
                    "description": "Ejecuta la tarea principal del flujo fallback",
                }
            ],
            "nodes": [
                {
                    "id": "inicio",
                    "type": "start",
                    "name": "Inicio",
                    "description": "Inicio del flujo",
                },
                {
                    "id": "procesar_solicitud",
                    "type": "task",
                    "name": "Procesar solicitud",
                    "description": objetivo,
                    "responsibleRoleId": "operador",
                    "responsibleType": "department",
                    "departmentHint": "Administracion",
                },
                {
                    "id": "fin",
                    "type": "end",
                    "name": "Fin",
                    "description": "Fin del flujo",
                },
            ],
            "transitions": [
                {
                    "id": "tr_inicio_procesar",
                    "from": "inicio",
                    "to": "procesar_solicitud",
                    "label": "continuar",
                    "condition": None,
                },
                {
                    "id": "tr_procesar_fin",
                    "from": "procesar_solicitud",
                    "to": "fin",
                    "label": "finalizar",
                    "condition": None,
                },
            ],
            "forms": [],
            "businessRules": [],
            "analysis": {
                "summary": "Workflow fallback lineal generado localmente por error del proveedor IA",
                "assumptions": [
                    "Se genero un flujo minimo por contingencia",
                ],
                "warnings": [
                    "La salida fue generada sin interpretacion completa del proceso por parte de la IA",
                ],
                "complexity": "low",
            },
        }
