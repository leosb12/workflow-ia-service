from app.core.config import get_settings
from app.modules.user_guide.admin.admin_guide_fallback_service import (
    AdminGuideFallbackService,
)
from app.modules.user_guide.admin.admin_guide_intent_classifier import (
    AdminGuideIntentClassifier,
)
from app.modules.user_guide.admin.admin_guide_prompts import AdminGuidePrompts
from app.modules.user_guide.admin.admin_guide_service import AdminGuideService
from app.modules.user_guide.employee.employee_guide_fallback_service import (
    EmployeeGuideFallbackService,
)
from app.modules.user_guide.employee.employee_guide_intent_classifier import (
    EmployeeGuideIntentClassifier,
)
from app.modules.user_guide.employee.employee_guide_prompts import EmployeeGuidePrompts
from app.modules.user_guide.employee.employee_guide_service import EmployeeGuideService
from app.shared.llm.json_parser import JsonObjectParser
from app.shared.llm.llm_client import DeepSeekClient
from app.shared.llm.prompt_runner import PromptRunner


def get_admin_guide_service() -> AdminGuideService:
    settings = get_settings()
    llm_client = DeepSeekClient(settings=settings)
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = AdminGuidePrompts()
    classifier = AdminGuideIntentClassifier()
    fallback_service = AdminGuideFallbackService()
    return AdminGuideService(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        classifier=classifier,
        fallback_service=fallback_service,
        llm_model=settings.deepseek_user_guide_model,
    )


def get_employee_guide_service() -> EmployeeGuideService:
    settings = get_settings()
    llm_client = DeepSeekClient(settings=settings)
    prompt_runner = PromptRunner(llm_client=llm_client)
    json_parser = JsonObjectParser()
    prompts = EmployeeGuidePrompts()
    classifier = EmployeeGuideIntentClassifier()
    fallback_service = EmployeeGuideFallbackService()
    return EmployeeGuideService(
        prompt_runner=prompt_runner,
        json_parser=json_parser,
        prompts=prompts,
        classifier=classifier,
        fallback_service=fallback_service,
        llm_model=settings.deepseek_user_guide_model,
    )
