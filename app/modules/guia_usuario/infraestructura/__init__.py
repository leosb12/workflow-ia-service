from app.modules.guia_usuario.infraestructura.dependencias import (
    obtener_servicio_guia_administrador,
    obtener_servicio_guia_funcionario,
    obtener_servicio_guia_usuario_movil,
)

get_servicio_guia_administrador = obtener_servicio_guia_administrador
get_servicio_guia_funcionario = obtener_servicio_guia_funcionario
get_servicio_guia_usuario_movil = obtener_servicio_guia_usuario_movil

__all__ = [
    "obtener_servicio_guia_administrador",
    "obtener_servicio_guia_funcionario",
    "obtener_servicio_guia_usuario_movil",
    "get_servicio_guia_administrador",
    "get_servicio_guia_funcionario",
    "get_servicio_guia_usuario_movil",
]
