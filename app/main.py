from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.ia.controller.ia_controller import router as ia_router


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="1.0.0",
        description="Servicio de IA para workflows de politicas de negocio.",
    )

    register_exception_handlers(app)
    app.include_router(ia_router)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": settings.app_name, "env": settings.app_env}

    return app


app = create_app()
