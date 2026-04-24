from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


SeverityLevel = Literal["LOW", "MEDIUM", "HIGH"]
PriorityLevel = Literal["LOW", "MEDIUM", "HIGH"]


class BottleneckItem(BaseModel):
    type: Literal["NODE", "DEPARTMENT", "OFFICIAL", "POLICY", "TASK"]
    name: str = Field(min_length=1, max_length=200)
    severity: SeverityLevel
    evidence: str = Field(min_length=1, max_length=500)
    impact: str = Field(min_length=1, max_length=500)
    recommendation: str = Field(min_length=1, max_length=500)

    model_config = ConfigDict(extra="forbid")


class BottleneckAnalysisResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    bottlenecks: list[BottleneckItem] = Field(default_factory=list)
    source: str = "AI"
    available: bool = True

    model_config = ConfigDict(
        extra="forbid",
        json_schema_extra={
            "example": {
                "summary": "Revision documental concentra la mayor demora y acumulacion.",
                "bottlenecks": [
                    {
                        "type": "NODE",
                        "name": "Revision documental",
                        "severity": "HIGH",
                        "evidence": "Es la actividad mas lenta y mantiene tareas pendientes antiguas.",
                        "impact": "Puede retrasar el avance general de los tramites.",
                        "recommendation": "Revisar asignacion de carga o dividir la actividad.",
                    }
                ],
                "source": "AI",
                "available": True,
            }
        },
    )


class TaskRedistributionItem(BaseModel):
    from_official: str = Field(alias="fromOfficial", min_length=1, max_length=200)
    to_official: str = Field(alias="toOfficial", min_length=1, max_length=200)
    reason: str = Field(min_length=1, max_length=500)
    priority: PriorityLevel
    expected_impact: str = Field(alias="expectedImpact", min_length=1, max_length=500)

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class TaskRedistributionResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    recommendations: list[TaskRedistributionItem] = Field(default_factory=list)
    source: str = "AI"
    available: bool = True

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PolicyIssueItem(BaseModel):
    node_or_step: str = Field(alias="nodeOrStep", min_length=1, max_length=200)
    problem: str = Field(min_length=1, max_length=500)
    evidence: str = Field(min_length=1, max_length=500)
    recommendation: str = Field(min_length=1, max_length=500)
    priority: PriorityLevel

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class PolicyImprovementResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=500)
    policy_issues: list[PolicyIssueItem] = Field(default_factory=list, alias="policyIssues")
    source: str = "AI"
    available: bool = True

    model_config = ConfigDict(populate_by_name=True, extra="forbid")


class IntelligentSummaryResponse(BaseModel):
    bottlenecks: BottleneckAnalysisResponse
    task_redistribution: TaskRedistributionResponse = Field(alias="taskRedistribution")
    policy_improvement: PolicyImprovementResponse | None = Field(default=None, alias="policyImprovement")

    model_config = ConfigDict(populate_by_name=True, extra="forbid")
