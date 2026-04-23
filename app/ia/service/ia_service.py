import json
import logging
from json import JSONDecodeError
from typing import Any

from pydantic import ValidationError
from starlette.status import HTTP_400_BAD_REQUEST, HTTP_502_BAD_GATEWAY

from app.core.exceptions import ApiException
from app.ia.client.deepseek_client import DeepSeekClient
from app.ia.dto.deepseek import DeepSeekMessage
from app.ia.dto.texto_a_flujo import (
    GenerationContext,
    TextoAFlujoRequest,
    TextoAFlujoResponse,
)
from app.ia.util.workflow_validator import WorkflowJsonValidator

log = logging.getLogger(__name__)


class IaService:
    MAX_INTENTOS_IA = 3
    MAX_RAW_REINTENTO = 5000

    def __init__(
        self,
        deepseek_client: DeepSeekClient,
        workflow_validator: WorkflowJsonValidator,
    ) -> None:
        self.deepseek_client = deepseek_client
        self.workflow_validator = workflow_validator

    async def convertir_texto_a_flujo(
        self,
        request: TextoAFlujoRequest,
    ) -> TextoAFlujoResponse:
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
        system_prompt = self._construir_system_prompt()
        user_prompt = self._construir_user_prompt(descripcion, context)

        ultimo_error: Exception | None = None
        ultimo_raw: str = ""

        for intento in range(1, self.MAX_INTENTOS_IA + 1):
            raw_json = ""
            try:
                messages = [
                    DeepSeekMessage(role="system", content=system_prompt),
                    DeepSeekMessage(role="user", content=user_prompt),
                ]
                raw_json = await self.deepseek_client.generar_json(messages)
                workflow = self._parse_workflow_json(raw_json)
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
                    user_prompt = self._construir_prompt_reintento(
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

    def _parse_workflow_json(self, raw_json: str) -> dict[str, Any]:
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
                log.warning("La IA devolvio contenido no parseable: %s", exc)
                raise ApiException(
                    HTTP_502_BAD_GATEWAY,
                    "DeepSeek devolvio JSON invalido",
                ) from exc

            try:
                parsed = json.loads(extracted)
            except JSONDecodeError as second_exc:
                log.warning("No se pudo parsear el JSON extraido: %s", second_exc)
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
                    "aliases": ["administración"],
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

    def _construir_system_prompt(self) -> str:
        return """
Eres un generador experto de workflows de politicas de negocio con semantica estricta de diagrama de actividades UML.

Tu unica salida debe ser un objeto JSON valido.
No uses markdown.
No uses comentarios.
No escribas texto antes ni despues del JSON.

La salida debe tener EXACTAMENTE estas claves de primer nivel:
policy, departments, roles, nodes, transitions, forms, businessRules, analysis

ESTRUCTURA REQUERIDA:

{
  "policy": {
    "name": "string",
    "description": "string",
    "objective": "string",
    "version": "1.0"
  },
    "departments": [
        {
            "id": "string",
            "name": "string",
            "description": "string",
            "aliases": []
        }
    ],
  "roles": [
    {
      "id": "string",
      "name": "string",
      "description": "string"
    }
  ],
  "nodes": [
    {
      "id": "string",
      "type": "start|task|decision|parallel_start|parallel_end|end",
      "name": "string",
      "description": "string",
      "responsibleRoleId": "string",
      "formId": "string",
            "decisionCriteria": "string",
            "responsibleType": "department|initiator",
            "departmentHint": "string"
    }
  ],
  "transitions": [
    {
      "id": "string",
      "from": "string",
      "to": "string",
      "label": "string",
      "condition": "string|null"
    }
  ],
  "forms": [
    {
      "id": "string",
      "nodeId": "string",
      "name": "string",
      "fields": [
        {
          "id": "string",
          "label": "string",
                    "type": "text|textarea|number|date|select|file|boolean|email|phone|currency",
          "required": true,
          "options": []
        }
      ]
    }
  ],
  "businessRules": [
    {
      "id": "string",
      "name": "string",
      "description": "string",
      "appliesToNodeId": "string",
      "expression": "string",
      "severity": "blocking|warning"
    }
  ],
  "analysis": {
    "summary": "string",
    "assumptions": [],
    "warnings": [],
    "complexity": "low|medium|high"
  }
}

REGLAS OBLIGATORIAS:

1. FORMATO
- El primer caracter de la respuesta debe ser {
- El JSON debe ser valido
- Todas las claves de primer nivel deben existir siempre
- Usa arrays vacios si no hay departments, forms, businessRules, assumptions o warnings

1.1 DEPARTAMENTOS
- Identifica todos los departamentos necesarios a partir de la descripcion
- Reutiliza nombres de departamentos cuando coincidan o sean muy parecidos a los ya existentes en el contexto del frontend
- Si el contexto incluye departamentos existentes, preferir match por similitud semantica antes de proponer uno nuevo
- Si un departamento no existe en el contexto y es necesario para el workflow, incluyelo en departments
- Mantener nombres de departamento en espanol claro y breve: solicitante, admision, aprobador, finanzas, rrhh, control, etc.
- Usa ids unicos en snake_case para los departamentos
- Incluye aliases solo si ayudan a reconocer sinonimos o nombres parecidos

2. NODOS
- Debe existir exactamente 1 nodo start y al menos 1 nodo end
- Tipos permitidos: start, task, decision, parallel_start, parallel_end, end
- Todo nodo task debe tener responsibleRoleId valido
- Todo nodo task debe incluir responsibleType obligatorio: "department" o "initiator"
- Si responsibleType = "department", incluir departmentHint con el nombre del departamento esperado
- Si responsibleType = "initiator", NO incluir departmentHint
- Usa responsibleType = "initiator" unica y exclusivamente cuando la tarea consista en pedir al cliente o solicitante un dato, respuesta, declaracion o documento que solo esa persona conoce, posee o puede confirmar
- No uses responsibleType = "initiator" para validaciones, revisiones, aprobaciones, controles, registros, derivaciones o decisiones internas
- Si un area interna revisa, valida o decide sobre informacion, el responsable es ese departamento aunque el dato original venga del cliente
- Evita asignar por defecto "quien inicio el tramite"; si hay duda entre iniciador y departamento, prioriza el departamento que ejecuta la accion
- responsibleRoleId debe corresponder al rol mas apropiado para la tarea; si el rol representa el area humana, reutilizalo sin duplicar departamentos
- Todo task que capture, revise, valide, evalue, inspeccione, corrija o subsane datos debe tener formId
- Los nodos start, end, decision, parallel_start y parallel_end no deben tener responsibleRoleId
- Los nodos start, end, decision, parallel_start y parallel_end no deben tener formId
- Los nodos start, end, decision, parallel_start y parallel_end no deben tener responsibleType ni departmentHint
- Omitir responsibleRoleId, formId y decisionCriteria cuando no apliquen
- No uses null en campos opcionales que no apliquen

3. DECISIONES
- Todo decision debe tener al menos 2 transiciones salientes
- Todas las transiciones salientes de decision deben tener condition no nula
- En decisiones binarias, usar ramas SI y NO (o equivalente) en label y/o condition
- Las condiciones deben ser claras y mutuamente excluyentes
- Si la decision depende de datos de formularios, usa nombres consistentes con los field.id
- Si aplica, incluir decisionCriteria

4. PARALELISMO
- Todo parallel_start debe tener al menos 2 ramas salientes
- Todo parallel_start debe cerrarse con un parallel_end correspondiente
- Las ramas paralelas deben converger primero en parallel_end antes de continuar
- Nunca conectes tareas paralelas directamente a un decision

5. TRANSICIONES
- Toda transition.from y transition.to deben existir en nodes
- No debe haber nodos huerfanos
- El flujo debe ser alcanzable desde start hasta end
- Evita caminos muertos
- label debe ser un string descriptivo y no vacio

6. FORMULARIOS
- Incluir forms solo si la descripcion exige captura de datos claramente
- Todo form.nodeId debe referenciar un nodo task existente
- Todo form.fields debe ser siempre un array
- Nunca devolver fields como null, string u objeto
- Los field.id deben ser unicos globalmente en toda la salida
- Usa tipos coherentes: boolean para aprobacion/cumplimiento, file para adjuntos/fotos/planos/evidencias, textarea para observaciones o texto largo
- Si la actividad requiere captura o revision de informacion, crear al menos 2 campos de formulario utiles

7. ROLES
- Reutiliza roles
- No crees roles duplicados o innecesarios
- Los nombres de rol deben ser concretos y alineados al dominio (ej: Solicitante, Mesa de Entrada, Administracion, Finanzas, RRHH)

8. BUSINESS RULES
- Incluir solo si la descripcion menciona reglas explicitas
- No inventar reglas complejas

9. ANALYSIS
- Debe ser breve y util
- summary debe resumir el flujo en pocas lineas
- assumptions debe incluir solo lo minimo necesario
- warnings debe incluir ambiguedades relevantes
- complexity:
  - low: flujo lineal
  - medium: decisiones o loops
  - high: paralelismo o multiples loops o decisiones complejas

10. MODELADO
- No inventes pasos que no existen
- No omitas validaciones mencionadas
- No mezcles acciones distintas en una sola tarea si cambia la responsabilidad o el objetivo
- Usa el menor numero de nodos posible sin perder logica
- Mantiene nombres y textos en espanol claro
- Usa ids unicos en snake_case, sin espacios ni acentos
- Evita loops innecesarios; si hay subsanacion, modela una rama de retorno explicita con condicion

OBJETIVO DE CALIDAD:
Genera un workflow compacto, consistente, validable y apto para ser consumido por un backend y por un frontend con swimlanes por departamento.
""".strip()

    def _construir_user_prompt(
        self,
        descripcion: str,
        context: GenerationContext | None,
    ) -> str:
        context_block = self._construir_contexto_prompt(context)

        return f"""
Genera el workflow completo a partir de esta descripcion:

{descripcion}

{context_block}
""".strip()

    def _construir_contexto_prompt(self, context: GenerationContext | None) -> str:
        if not context or not context.departamentos:
            return "Contexto adicional: no se recibieron departamentos del frontend."

        lines = [
            "Contexto del frontend (departamentos disponibles):",
        ]

        for departamento in context.departamentos:
            lines.append(f"- {departamento.nombre} (id: {departamento.id})")

        lines.append(
            "Regla: en nodos task con responsibleType=department, usa departmentHint coherente con esta lista."
        )

        return "\n".join(lines)

    def _construir_prompt_reintento(
        self,
        descripcion: str,
        context: GenerationContext | None,
        raw_prev: str,
        error: str,
        intento: int,
    ) -> str:
        raw_resumido = (raw_prev or "").strip()
        if len(raw_resumido) > self.MAX_RAW_REINTENTO:
            raw_resumido = raw_resumido[: self.MAX_RAW_REINTENTO]

        return f"""
Reintento {intento}.
Devuelve SOLO un JSON valido.
No uses markdown.
No uses comentarios.
No agregues explicaciones.
Prioriza validez estructural, consistencia de ids y cumplimiento de reglas UML.
Recuerda: usa responsibleType = "initiator" solo cuando se le pide al cliente o solicitante un dato o documento que solo esa persona puede aportar; revisiones, validaciones y aprobaciones internas corresponden al departamento responsable.

Error detectado:
{error}

Salida previa:
{raw_resumido or "<sin salida previa>"}

Corrige completamente la salida y devuelve un unico JSON final valido para esta descripcion:

{descripcion}

{self._construir_contexto_prompt(context)}
""".strip()
