from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import configure_security
from app.modules.workflow_generator.controller import router as workflow_generator_router


def create_app() -> FastAPI:
    configure_logging()
    settings = get_settings()

    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Servicio de IA para workflows de politicas de negocio.",
    )

    configure_security(app)
    register_exception_handlers(app)
    app.include_router(workflow_generator_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "env": settings.app_env,
        }

    return app


app = create_app()
