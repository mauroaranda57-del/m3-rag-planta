"""
main.py — Pruebas del sistema RAG.
1. Pregunta cuya respuesta ESTÁ en los documentos.
2. "Pregunta trampa" cuya respuesta NO está: el modelo debe decir que no tiene esa información.
"""
import asyncio
import logging

from dotenv import load_dotenv

from rag import get_rag_response

logging.basicConfig(level=logging.INFO, format="%(levelname)s | %(name)s | %(message)s")
for noisy in ("httpx", "chromadb", "google_genai"):
    logging.getLogger(noisy).setLevel(logging.WARNING)

PREGUNTAS = [
    ("EN LOS DOCUMENTOS", "¿Qué aceite usa la bomba BC-200 y cada cuánto se cambia?"),
    ("EN LOS DOCUMENTOS", "¿Qué pasa si el pesaje del camión difiere del peso teórico?"),
    ("PREGUNTA TRAMPA", "¿Cuál es la presión de trabajo del compresor de la sala 2?"),
]


async def main():
    load_dotenv()
    for tipo, pregunta in PREGUNTAS:
        print(f"\n=== {tipo} ===\nPregunta: {pregunta}")
        try:
            r = await get_rag_response(pregunta)
            print(r.model_dump_json(indent=2))
        except Exception as e:
            print(f"Falló después de los reintentos: {type(e).__name__}: {e}")


if __name__ == "__main__":
    asyncio.run(main())
