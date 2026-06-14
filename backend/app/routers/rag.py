from fastapi import APIRouter
from pydantic import BaseModel
from openai import OpenAI
from qdrant_client import QdrantClient
from app.config import settings

router = APIRouter(prefix="/api/rag", tags=["rag"])


class RAGRequest(BaseModel):
    query: str
    project_id: str | None = None


@router.post("/query")
async def rag_query(request: RAGRequest):
    openai_client = OpenAI(api_key=settings.openai_api_key)
    qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    response = openai_client.embeddings.create(
        input=request.query,
        model="text-embedding-3-small"
    )
    vec = response.data[0].embedding

    results = qdrant.search(
        collection_name=settings.qdrant_collection,
        query_vector=vec,
        limit=5,
        with_payload=True,
    )

    context_chunks = [
        {
            "title": r.payload.get("title"),
            "text": r.payload.get("text"),
            "score": round(r.score, 3),
            "doc_type": r.payload.get("document_type"),
        }
        for r in results if r.score > 0.30
    ]

    if not context_chunks:
        return {"answer": "No relevant documents found.", "sources": []}

    context_text = "\n\n".join(
        f"[{c['title']}]\n{c['text']}" for c in context_chunks
    )

    answer_response = openai_client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {
                "role": "system",
                "content": "You are a construction project analyst. Answer questions using only the provided document context. Cite the source document by title.",
            },
            {
                "role": "user",
                "content": f"Context:\n{context_text}\n\nQuestion: {request.query}",
            },
        ],
        temperature=0,
    )

    return {
        "answer": answer_response.choices[0].message.content,
        "sources": context_chunks,
    }
