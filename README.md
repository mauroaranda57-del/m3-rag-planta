# Pre-entrega 3 · Sistema de recuperación semántica local (RAG)

Asistente técnico de planta que responde preguntas **únicamente** a partir de documentos internos
(manual de mantenimiento de bomba, procedimiento de almacenamiento y despacho, instructivo de EPP).
Si la respuesta no está en los documentos, lo dice en lugar de inventar.

## Estructura

| Archivo / carpeta | Qué hace |
|---|---|
| `data/` | Dataset de ejemplo: 3 documentos `.md` de una planta industrial |
| `ingest.py` | Ingesta: lee `data/`, fragmenta (`RecursiveCharacterTextSplitter`, ~500 tokens / 50 overlap), genera embeddings (Gemini) y persiste en ChromaDB (`./vectorstore`). Si la base ya existe, no reindexa |
| `schemas.py` | `RespuestaRAG` (Pydantic): `respuesta`, `encontrado_en_contexto`, `referencias` |
| `rag.py` | Retriever (top_k=4) + prompt grounded + LLM async + `PydanticOutputParser` + `.with_retry()`; expone `get_rag_response(query)` |
| `main.py` | Pruebas: dos preguntas con respuesta en los documentos y una pregunta trampa |

## Cadena LCEL

```python
chain = (
    {"context": retriever | RunnableLambda(format_docs), "question": RunnablePassthrough()}
    | prompt
    | model
    | PydanticOutputParser(pydantic_object=RespuestaRAG)
).with_retry(stop_after_attempt=3)
```

## Decisiones de diseño

- **Mismo modelo de embeddings** (`gemini-embedding-001`) para indexar y consultar; está centralizado en `ingest.get_embeddings()`.
- **Chunking por estructura**: los separadores priorizan títulos `## ` y párrafos antes que cortar por palabras, así los fragmentos conservan secciones completas del manual.
- **top_k = 4** para evitar el "contexto infinito".
- **Persistencia**: `ingest.py` verifica si la colección ya tiene documentos antes de reindexar; `--rebuild` fuerza la reindexación.
- **Prompt filtro de veracidad**: el system prompt exige responder solo con el CONTEXTO y devolver `encontrado_en_contexto=false` con `referencias=[]` cuando no hay información.

## Instalación

```bash
python -m venv .venv
.venv\Scripts\activate          # Linux/Mac: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env          # y completá GEMINI_API_KEY
```

## Ejecución

```bash
python ingest.py     # 1) indexa los documentos en ./vectorstore (solo la primera vez)
python main.py       # 2) corre las preguntas de prueba
```

## Ejemplo de salida

Pregunta con respuesta en los documentos:
```json
{
  "respuesta": "La bomba BC-200 usa aceite ISO VG 68 y se cambia cada 4.000 horas de operación o cada 6 meses, lo que ocurra primero.",
  "encontrado_en_contexto": true,
  "referencias": ["manual_mantenimiento_bomba.md"]
}
```

Pregunta trampa:
```json
{
  "respuesta": "No tengo acceso a esa información: el contexto no menciona la presión de trabajo del compresor de la sala 2.",
  "encontrado_en_contexto": false,
  "referencias": []
}
```

## Variables de entorno

| Variable | Descripción |
|---|---|
| `GEMINI_API_KEY` | Clave de Google AI Studio (gratuita) |
| `LLM_PROVIDER` | `gemini` por defecto |
| `LLM_MODEL` / `EMBEDDING_MODEL` | Opcionales |
