from pydantic import BaseModel, ConfigDict, Field


class SimulationAnalysisResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=1800)
    source: str = "AI"
    available: bool = True
    recommendations: list[str] = Field(default_factory=list)
    detected_issues: list[str] = Field(default_factory=list, alias="detectedIssues")
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    bottlenecks: list[str] = Field(default_factory=list)
    efficiency_score: float | None = Field(default=None, alias="efficiencyScore")
    executive_conclusion: str | None = Field(default=None, alias="executiveConclusion", max_length=1400)

    model_config = ConfigDict(populate_by_name=True, extra="allow")


class SimulationComparisonResponse(BaseModel):
    summary: str = Field(min_length=1, max_length=1800)
    source: str = "AI"
    available: bool = True
    recommendations: list[str] = Field(default_factory=list)
    detected_issues: list[str] = Field(default_factory=list, alias="detectedIssues")
    strengths: list[str] = Field(default_factory=list)
    risks: list[str] = Field(default_factory=list)
    efficiency_score: float | None = Field(default=None, alias="efficiencyScore")
    executive_conclusion: str | None = Field(default=None, alias="executiveConclusion", max_length=1400)
    more_efficient_policy_id: str | None = Field(default=None, alias="moreEfficientPolicyId")
    more_efficient_policy_name: str | None = Field(default=None, alias="moreEfficientPolicyName")

    model_config = ConfigDict(populate_by_name=True, extra="allow")
