"""
schemas.py — Formato de la respuesta del sistema RAG.
"""
from pydantic import BaseModel, Field


class RespuestaRAG(BaseModel):
    """Respuesta validada que devuelve get_rag_response()."""
    respuesta: str = Field(
        description="Respuesta en español basada EXCLUSIVAMENTE en el contexto. "
                    "Si la información no está en el contexto, decir claramente que no se tiene acceso a esa información."
    )
    encontrado_en_contexto: bool = Field(
        description="True si la respuesta está respaldada por el contexto; False si el contexto no contiene la información."
    )
    referencias: list[str] = Field(
        default_factory=list,
        description="Nombres de los documentos fuente que respaldan la respuesta. Lista vacía si no se encontró.",
    )
