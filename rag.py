"""
rag.py — Cadena RAG asíncrona (retriever + prompt grounded + LLM + PydanticOutputParser).

    get_rag_response(query)
        a. búsqueda de similitud en ChromaDB (top_k=4)
        b. arma el prompt con los fragmentos recuperados como CONTEXTO
        c. llama al LLM de forma asíncrona (ainvoke)
        d. parsea la respuesta a RespuestaRAG (Pydantic) con reintentos
"""
import logging
import os

from langchain_core.documents import Document
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnablePassthrough, RunnableLambda

from ingest import ingest
from schemas import RespuestaRAG

logger = logging.getLogger(__name__)

TOP_K = 4  # entre 3 y 5: evita el "contexto infinito" / lost in the middle


def get_model():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()
    model_name = os.getenv("LLM_MODEL") or {"gemini": "gemini-3.6-flash", "openai": "gpt-4o-mini",
                                           "anthropic": "claude-3-5-haiku-latest"}[provider]
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model_name, google_api_key=os.environ["GEMINI_API_KEY"])
    if provider == "openai":
        from langchain_openai import ChatOpenAI
        return ChatOpenAI(model=model_name, temperature=0)
    if provider == "anthropic":
        from langchain_anthropic import ChatAnthropic
        return ChatAnthropic(model=model_name, temperature=0)
    raise ValueError(f"Proveedor no soportado: {provider}")


# ---------- Parser Pydantic ----------
parser = PydanticOutputParser(pydantic_object=RespuestaRAG)

# ---------- Prompt "filtro de veracidad" ----------
prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sos un asistente técnico de una planta industrial. Respondé ÚNICAMENTE basándote en el CONTEXTO "
        "proporcionado, que proviene de manuales y procedimientos internos. "
        "Si la respuesta no está en el contexto, decí claramente que no tenés acceso a esa información, "
        "poné encontrado_en_contexto en false y dejá referencias vacía. No inventes datos, valores ni procedimientos. "
        "Cuando respondas, citá en 'referencias' los nombres de los documentos de donde sacaste la información.\n\n"
        "{format_instructions}",
    ),
    (
        "human",
        "CONTEXTO:\n{context}\n\nPREGUNTA: {question}",
    ),
]).partial(format_instructions=parser.get_format_instructions())


def format_docs(docs: list[Document]) -> str:
    """Transformador de documentos: convierte los fragmentos en un bloque de texto con su fuente."""
    return "\n\n".join(
        f"[Documento: {d.metadata.get('source', '?')} | fragmento {d.metadata.get('chunk_id', '?')}]\n{d.page_content}"
        for d in docs
    )


def build_chain():
    store = ingest()  # devuelve la base existente (o la crea si no está)
    retriever = store.as_retriever(search_kwargs={"k": TOP_K})
    model = get_model()

    # LCEL: {context, question} -> prompt -> LLM -> PydanticOutputParser
    chain = (
        {
            "context": retriever | RunnableLambda(format_docs),
            "question": RunnablePassthrough(),
        }
        | prompt
        | model
        | parser
    )
    return chain.with_retry(stop_after_attempt=3, wait_exponential_jitter=True), retriever


_chain = None
_retriever = None


async def get_rag_response(query: str) -> RespuestaRAG:
    global _chain, _retriever
    if _chain is None:
        _chain, _retriever = build_chain()

    docs = await _retriever.ainvoke(query)
    logger.info("Recuperados %d fragmentos: %s", len(docs),
                ", ".join(f"{d.metadata['source']}#{d.metadata['chunk_id']}" for d in docs))

    respuesta: RespuestaRAG = await _chain.ainvoke(query)
    logger.info("encontrado_en_contexto=%s | referencias=%s", respuesta.encontrado_en_contexto, respuesta.referencias)
    return respuesta
