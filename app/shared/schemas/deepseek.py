from pydantic import BaseModel, ConfigDict, Field


class DeepSeekMessage(BaseModel):
    role: str
    content: str


class ResponseFormat(BaseModel):
    type: str


class DeepSeekRequest(BaseModel):
    model: str
    messages: list[DeepSeekMessage]
    response_format: ResponseFormat
    max_tokens: int | None = Field(default=None, alias="max_tokens")
    temperature: float
    stream: bool = False

    model_config = ConfigDict(populate_by_name=True)


class DeepSeekResponseMessage(BaseModel):
    role: str | None = None
    content: str | None = None
    reasoning_content: str | None = None


class DeepSeekChoice(BaseModel):
    index: int | None = None
    message: DeepSeekResponseMessage | None = None
    finish_reason: str | None = None


class DeepSeekResponse(BaseModel):
    choices: list[DeepSeekChoice] = Field(default_factory=list)
