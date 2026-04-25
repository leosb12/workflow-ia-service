from app.shared.llm.llm_client import DeepSeekClient
from app.shared.schemas.deepseek import DeepSeekMessage


class PromptRunner:
    def __init__(self, llm_client: DeepSeekClient) -> None:
        self.llm_client = llm_client

    async def run_json_prompt(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        model_override: str | None = None,
    ) -> str:
        messages = [
            DeepSeekMessage(role="system", content=system_prompt),
            DeepSeekMessage(role="user", content=user_prompt),
        ]
        return await self.llm_client.generar_json(
            messages,
            model_override=model_override,
        )
