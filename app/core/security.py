from collections.abc import Sequence

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


DEFAULT_CORS_ORIGINS: Sequence[str] = (
    "http://localhost:4200",
    "http://127.0.0.1:4200",
)


def configure_security(app: FastAPI) -> None:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(DEFAULT_CORS_ORIGINS),
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
