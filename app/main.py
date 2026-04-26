from fastapi import FastAPI

from app.core.config import get_settings
from app.core.exceptions import register_exception_handlers
from app.core.logging import configure_logging
from app.core.security import configure_security
from app.modules.analitica.controlador import router as router_analitica
from app.modules.asistente_formularios.controlador import router as router_asistente_formularios
from app.modules.simulacion.controlador import router as router_simulacion
from app.modules.guia_usuario.controlador import router as router_guia_usuario
from app.modules.generador_flujos.controlador import router as router_generador_flujos
from app.modules.editor_flujo_ia.controlador import router as router_editor_flujo_ia


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
    app.include_router(router_generador_flujos)
    app.include_router(router_asistente_formularios)
    app.include_router(router_analitica)
    app.include_router(router_simulacion)
    app.include_router(router_guia_usuario)
    app.include_router(router_editor_flujo_ia)

    @app.get("/health", tags=["health"])
    async def health() -> dict[str, str]:
        return {
            "status": "ok",
            "service": settings.app_name,
            "env": settings.app_env,
        }

    return app


app = create_app()
