"""
ingest.py — Módulo de ingesta (setup del "cerebro").

1. Lee todos los .md / .txt de la carpeta ./data
2. Los fragmenta con RecursiveCharacterTextSplitter (chunking)
3. Convierte cada fragmento en embedding (Gemini) y lo persiste en ChromaDB (./vectorstore)

Si la base ya existe y tiene documentos, NO vuelve a indexar (a menos que se pase --rebuild).

Uso:
    python ingest.py            # indexa solo si la base está vacía
    python ingest.py --rebuild  # borra y reindexa todo
"""
import logging
import os
import shutil
import sys
from pathlib import Path

from dotenv import load_dotenv
from langchain_chroma import Chroma
from langchain_core.documents import Document
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(message)s")
logger = logging.getLogger(__name__)

DATA_DIR = Path("data")
VECTORSTORE_DIR = "./vectorstore"
COLLECTION_NAME = "planta_docs"

# ~500 tokens ≈ 2000 caracteres en español; overlap de ~50 tokens ≈ 200 caracteres
CHUNK_SIZE = 2000
CHUNK_OVERLAP = 200


def get_embeddings() -> GoogleGenerativeAIEmbeddings:
    """
    El MISMO modelo de embeddings se usa para indexar (acá) y para consultar (rag.py).
    Si no coinciden, las distancias vectoriales no tienen sentido.
    """
    return GoogleGenerativeAIEmbeddings(
        model=os.getenv("EMBEDDING_MODEL", "gemini-embedding-001"),
        google_api_key=os.environ["GEMINI_API_KEY"],
    )


def load_documents() -> list[Document]:
    docs = []
    for path in sorted(DATA_DIR.glob("*")):
        if path.suffix.lower() in {".md", ".txt"}:
            text = path.read_text(encoding="utf-8")
            docs.append(Document(page_content=text, metadata={"source": path.name}))
            logger.info("Leído %s (%d caracteres)", path.name, len(text))
    if not docs:
        raise SystemExit(f"No se encontraron .md/.txt en {DATA_DIR.resolve()}")
    return docs


def split_documents(docs: list[Document]) -> list[Document]:
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=CHUNK_SIZE,
        chunk_overlap=CHUNK_OVERLAP,
        separators=["\n## ", "\n\n", "\n", ". ", " ", ""],  # corta por secciones/párrafos antes que por palabras
    )
    chunks = splitter.split_documents(docs)
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = i
    logger.info("%d documentos -> %d fragmentos", len(docs), len(chunks))
    return chunks


def vectorstore_exists() -> bool:
    if not Path(VECTORSTORE_DIR).exists():
        return False
    try:
        store = Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTORSTORE_DIR,
            embedding_function=get_embeddings(),
        )
        return store._collection.count() > 0
    except Exception:
        return False


def ingest(rebuild: bool = False) -> Chroma:
    if rebuild and Path(VECTORSTORE_DIR).exists():
        logger.info("Borrando base existente en %s", VECTORSTORE_DIR)
        shutil.rmtree(VECTORSTORE_DIR)

    if not rebuild and vectorstore_exists():
        logger.info("La base vectorial ya existe en %s. No se reindexa (usá --rebuild para forzar).", VECTORSTORE_DIR)
        return Chroma(
            collection_name=COLLECTION_NAME,
            persist_directory=VECTORSTORE_DIR,
            embedding_function=get_embeddings(),
        )

    docs = load_documents()
    chunks = split_documents(docs)
    logger.info("Generando embeddings y guardando en ChromaDB...")
    store = Chroma.from_documents(
        documents=chunks,
        embedding=get_embeddings(),
        collection_name=COLLECTION_NAME,
        persist_directory=VECTORSTORE_DIR,
    )
    logger.info("Listo: %d fragmentos indexados en %s", store._collection.count(), VECTORSTORE_DIR)
    return store


if __name__ == "__main__":
    load_dotenv()
    ingest(rebuild="--rebuild" in sys.argv)
