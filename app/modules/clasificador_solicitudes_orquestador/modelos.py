from pydantic import BaseModel, ConfigDict, Field, field_validator
from typing import Any


class RequisitoInicialDto(BaseModel):
    nombre: str
    label: str | None = None
    tipo: str | None = None
    obligatorio: bool = False

    model_config = ConfigDict(extra="ignore")


class PoliticaClasificacionDto(BaseModel):
    id: str = Field(min_length=1)
    nombre: str = Field(min_length=1)
    descripcion: str | None = None
    categoria: str | None = None
    descripcionClasificacion: str | None = None
    palabrasClave: list[str] = Field(default_factory=list)
    intencionesEjemplo: list[str] = Field(default_factory=list)
    requisitosSugeridos: list[str] = Field(default_factory=list)
    requisitosIniciales: list[RequisitoInicialDto] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")

    @field_validator("id", "nombre")
    @classmethod
    def normalizar_obligatorios(cls, value: str) -> str:
        return value.strip()

    @field_validator("palabrasClave", "intencionesEjemplo", "requisitosSugeridos", mode="before")
    @classmethod
    def normalizar_listas(cls, value):
        if value is None:
            return []
        return [str(item).strip() for item in value if item and str(item).strip()]


class IaClasificacionRequest(BaseModel):
    texto: str = Field(min_length=1, max_length=4000)
    canal: str | None = None
    politicas: list[PoliticaClasificacionDto] = Field(min_length=1)
    usarDeepSeek: bool = False
    nombreDocumento: str | None = None

    model_config = ConfigDict(extra="ignore")

    @field_validator("texto")
    @classmethod
    def normalizar_texto(cls, value: str) -> str:
        return value.strip()


class TopResultadoClasificacionDto(BaseModel):
    politicaId: str
    nombrePolitica: str | None = None
    confianza: float
    scoreRequisitos: float | None = None
    scoreSemantico: float | None = None
    scoreFinal: float | None = None
    requisitosCoincidentes: list[str] = Field(default_factory=list)
    requisitosFaltantes: list[str] = Field(default_factory=list)

    model_config = ConfigDict(extra="ignore")


class IaClasificacionResponse(BaseModel):
    politicaId: str
    nombrePolitica: str | None = None
    confianza: float
    origen: str
    metodoRecomendacion: str | None = None
    requiereMasInformacion: bool = False
    requisitosDetectados: list[str] = Field(default_factory=list)
    requisitosCoincidentes: list[str] = Field(default_factory=list)
    requisitosFaltantes: list[str] = Field(default_factory=list)
    topResultados: list[TopResultadoClasificacionDto] = Field(default_factory=list)
    analisisDeepSeek: Any | None = None

    model_config = ConfigDict(extra="ignore")
