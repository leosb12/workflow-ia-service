from fastapi.testclient import TestClient

from app.main import app
from app.modules.analytics_ai.infrastructure.dependencies import get_analytics_ai_service
from app.modules.analytics_ai.schemas.analytics_response import (
    BottleneckAnalysisResponse,
    IntelligentSummaryResponse,
    PolicyImprovementResponse,
    TaskRedistributionResponse,
)


class StubAnalyticsAiService:
    async def analyze_bottlenecks(self, request):
        return BottleneckAnalysisResponse(
            summary="Resumen de cuellos de botella.",
            bottlenecks=[],
            source="AI",
            available=True,
        )

    async def recommend_task_redistribution(self, request):
        return TaskRedistributionResponse(
            summary="Resumen de redistribucion.",
            recommendations=[],
            source="AI",
            available=True,
        )

    async def improve_policy(self, request):
        return PolicyImprovementResponse(
            summary="Resumen de politica.",
            policyIssues=[],
            source="AI",
            available=True,
        )

    async def build_intelligent_summary(self, request):
        return IntelligentSummaryResponse(
            bottlenecks=await self.analyze_bottlenecks(request),
            taskRedistribution=await self.recommend_task_redistribution(request),
            policyImprovement=await self.improve_policy(None),
        )


def build_dashboard_body() -> dict:
    return {
        "general": {},
        "attentionTimes": {
            "averageByOfficial": [
                {"officialId": "user-1", "officialName": "Juan Perez", "averageHours": 6.3, "completedTasks": 12},
                {"officialId": "user-2", "officialName": "Ana Gomez", "averageHours": 3.1, "completedTasks": 20},
            ],
            "hasEnoughData": True,
        },
        "taskAccumulation": {
            "pendingByOfficial": [
                {"officialId": "user-1", "officialName": "Juan Perez", "pendingTasks": 8, "oldestTaskAgeHours": 36},
                {"officialId": "user-2", "officialName": "Ana Gomez", "pendingTasks": 2, "oldestTaskAgeHours": 8},
            ]
        },
    }


def test_analytics_routes_return_controlled_json() -> None:
    app.dependency_overrides[get_analytics_ai_service] = lambda: StubAnalyticsAiService()
    client = TestClient(app)

    bottlenecks = client.post("/api/ia/analytics/bottlenecks", json=build_dashboard_body())
    redistribution = client.post("/api/ia/analytics/task-redistribution", json=build_dashboard_body())
    policy = client.post(
        "/api/ia/analytics/policy-improvement",
        json={"dashboard": build_dashboard_body(), "policyName": "Solicitud de Credito"},
    )
    summary = client.post("/api/ia/analytics/intelligent-summary", json=build_dashboard_body())

    assert bottlenecks.status_code == 200
    assert bottlenecks.json()["available"] is True
    assert redistribution.status_code == 200
    assert redistribution.json()["source"] == "AI"
    assert policy.status_code == 200
    assert policy.json()["summary"] == "Resumen de politica."
    assert summary.status_code == 200
    assert "taskRedistribution" in summary.json()

    app.dependency_overrides.clear()
