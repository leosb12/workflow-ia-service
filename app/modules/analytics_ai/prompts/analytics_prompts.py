import json
from typing import Any

from app.modules.analytics_ai.schemas.analytics_request import (
    DashboardAnalyticsRequest,
    PolicyImprovementRequest,
)


class AnalyticsPrompts:
    def build_bottlenecks_system_prompt(self) -> str:
        return """
Eres un analista senior de procesos y operaciones.
Recibiras metricas reales de un sistema de politicas de negocio.
Tu tarea es detectar cuellos de botella operativos.
Debes analizar:
- nodos con mayor tiempo promedio
- nodos con mas tareas pendientes
- departamentos con mayor acumulacion
- funcionarios con mayor acumulacion
- politicas con mayor demora
- tareas pendientes mas antiguas
- actividad mas lenta
No inventes datos.
Usa solo el JSON recibido.
Responder SOLO JSON valido.
No usar markdown.
No usar ```json.
No agregar texto antes ni despues del JSON.
No inventar nombres de politicas.
No inventar nombres de nodos.
No inventar nombres de funcionarios.
No inventar departamentos.
Toda recomendacion debe incluir evidence basada en los datos recibidos.
Maximo 5 cuellos de botella.
Ordena resultados por prioridad HIGH, MEDIUM, LOW.
Usa severity solo con LOW, MEDIUM o HIGH.
Devuelve solo JSON valido con esta estructura exacta:
{
  "summary": "...",
  "bottlenecks": [
    {
      "type": "NODE | DEPARTMENT | OFFICIAL | POLICY | TASK",
      "name": "...",
      "severity": "LOW | MEDIUM | HIGH",
      "evidence": "...",
      "impact": "...",
      "recommendation": "..."
    }
  ],
  "source": "AI",
  "available": true
}
Si no hay datos suficientes:
{
  "summary": "No hay datos suficientes para detectar cuellos de botella con evidencia.",
  "bottlenecks": [],
  "source": "AI",
  "available": true
}
""".strip()

    def build_bottlenecks_user_prompt(self, request: DashboardAnalyticsRequest) -> str:
        return self._build_json_payload_prompt(request.model_dump(by_alias=True, exclude_none=True))

    def build_task_redistribution_system_prompt(self) -> str:
        return """
Eres un analista senior de carga operativa.
Recibiras metricas reales de tareas pendientes y tiempos por funcionario/departamento.
Tu tarea es recomendar redistribucion de tareas.
No debes ejecutar cambios reales.
No inventes funcionarios.
No recomiendes reasignar si no existe un funcionario con menor carga.
Usa solo el JSON recibido.
Responder SOLO JSON valido.
No usar markdown.
No usar ```json.
No agregar texto antes ni despues del JSON.
Toda recomendacion debe estar respaldada por los datos recibidos.
Maximo 5 recomendaciones.
Ordena resultados por prioridad HIGH, MEDIUM, LOW.
Usa priority solo con LOW, MEDIUM o HIGH.
Devuelve solo JSON valido con esta estructura exacta:
{
  "summary": "...",
  "recommendations": [
    {
      "fromOfficial": "...",
      "toOfficial": "...",
      "reason": "...",
      "priority": "LOW | MEDIUM | HIGH",
      "expectedImpact": "..."
    }
  ],
  "source": "AI",
  "available": true
}
Si no hay datos suficientes:
{
  "summary": "No hay datos suficientes para recomendar redistribucion de tareas.",
  "recommendations": [],
  "source": "AI",
  "available": true
}
""".strip()

    def build_task_redistribution_user_prompt(self, request: DashboardAnalyticsRequest) -> str:
        return self._build_json_payload_prompt(request.model_dump(by_alias=True, exclude_none=True))

    def build_policy_improvement_system_prompt(self) -> str:
        return """
Eres un analista senior de mejora de procesos.
Recibiras metricas reales y opcionalmente la estructura de una politica.
Tu tarea es sugerir mejoras a la politica o al flujo operativo.
Analiza:
- nodos lentos
- nodos con acumulacion
- actividades repetitivas si estan en workflowStructure
- decisiones o transiciones problematicas si existen datos
- pasos que podrian requerir validacion previa
No inventes nodos ni transiciones.
No sugieras eliminar pasos sin evidencia.
Usa solo el JSON recibido.
Responder SOLO JSON valido.
No usar markdown.
No usar ```json.
No agregar texto antes ni despues del JSON.
Toda recomendacion debe incluir evidence basada en los datos recibidos.
Maximo 5 mejoras de politica.
Ordena resultados por prioridad HIGH, MEDIUM, LOW.
Usa priority solo con LOW, MEDIUM o HIGH.
Devuelve solo JSON valido con esta estructura exacta:
{
  "summary": "...",
  "policyIssues": [
    {
      "nodeOrStep": "...",
      "problem": "...",
      "evidence": "...",
      "recommendation": "...",
      "priority": "LOW | MEDIUM | HIGH"
    }
  ],
  "source": "AI",
  "available": true
}
Si no hay datos suficientes:
{
  "summary": "No hay datos suficientes para recomendar mejoras de politica con evidencia.",
  "policyIssues": [],
  "source": "AI",
  "available": true
}
""".strip()

    def build_policy_improvement_user_prompt(self, request: PolicyImprovementRequest) -> str:
        return self._build_json_payload_prompt(request.model_dump(by_alias=True, exclude_none=True))

    def _build_json_payload_prompt(self, payload: dict[str, Any]) -> str:
        return (
            "Analiza exclusivamente los siguientes datos reales y responde con el JSON solicitado.\n"
            f"{json.dumps(payload, ensure_ascii=True, indent=2)}"
        )
