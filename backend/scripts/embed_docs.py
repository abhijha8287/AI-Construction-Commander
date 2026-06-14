"""
Phase 3: embed_docs.py
Chunks documents from PostgreSQL, embeds with OpenAI, upserts to Qdrant.
Verification: 3 semantic searches must return inspection report as top result.
"""
import asyncio
import os
import sys
import uuid

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy import text, update
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from openai import OpenAI
from app.config import settings

engine = create_async_engine(settings.database_url, echo=False)
Session = async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

CHUNK_SIZE = 500
CHUNK_OVERLAP = 50
VECTOR_DIM = 1536
EMBEDDING_MODEL = "text-embedding-3-small"


def chunk_text(text_content: str, size: int = CHUNK_SIZE, overlap: int = CHUNK_OVERLAP) -> list[str]:
    words = text_content.split()
    chunks = []
    i = 0
    while i < len(words):
        chunk = " ".join(words[i:i + size])
        chunks.append(chunk)
        i += size - overlap
    return chunks if chunks else [text_content]


async def embed():
    openai_client = OpenAI(api_key=settings.openai_api_key)
    qdrant = QdrantClient(host=settings.qdrant_host, port=settings.qdrant_port)

    # Create collection if not exists
    existing = [c.name for c in qdrant.get_collections().collections]
    if settings.qdrant_collection not in existing:
        qdrant.create_collection(
            collection_name=settings.qdrant_collection,
            vectors_config=VectorParams(size=VECTOR_DIM, distance=Distance.COSINE),
        )
        print(f"  Created Qdrant collection: {settings.qdrant_collection}")
    else:
        print(f"  Collection exists: {settings.qdrant_collection}")

    async with Session() as db:
        result = await db.execute(text(
            "SELECT id, project_id, document_type, title, content FROM documents WHERE embedding_status='pending'"
        ))
        docs = result.fetchall()

    print(f"  Found {len(docs)} documents to embed")

    points = []
    for doc in docs:
        doc_id, project_id, doc_type, title, content = doc
        if not content:
            print(f"  Skipping {title} — no content")
            continue

        chunks = chunk_text(content)
        print(f"  Embedding: {title} ({len(chunks)} chunk(s))")

        for i, chunk in enumerate(chunks):
            response = openai_client.embeddings.create(
                input=chunk,
                model=EMBEDDING_MODEL
            )
            vector = response.data[0].embedding
            point_id = str(uuid.uuid4())
            points.append(PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "doc_id": str(doc_id),
                    "project_id": str(project_id),
                    "document_type": doc_type,
                    "title": title,
                    "chunk_index": i,
                    "text": chunk,
                }
            ))

    if points:
        qdrant.upsert(collection_name=settings.qdrant_collection, points=points)
        print(f"  Upserted {len(points)} vectors to Qdrant")

    # Mark all docs as completed
    async with Session() as db:
        await db.execute(text(
            "UPDATE documents SET embedding_status='completed' WHERE embedding_status='pending'"
        ))
        await db.commit()

    # ── Verification ──────────────────────────────────────────────────────────
    print("\nPhase 3 verification (3 semantic searches):")

    test_queries = [
        ("yield strength failure", "ABC Steel Rebar Inspection"),
        ("shipment rejected", "ABC Steel Rebar Inspection"),
        ("inspection failure", "ABC Steel Rebar Inspection"),
    ]

    all_pass = True
    for query, expected_title_fragment in test_queries:
        response = openai_client.embeddings.create(input=query, model=EMBEDDING_MODEL)
        vec = response.data[0].embedding
        results = qdrant.search(
            collection_name=settings.qdrant_collection,
            query_vector=vec,
            limit=3,
            with_payload=True
        )
        if results:
            top = results[0]
            top_title = top.payload.get("title", "")
            score = top.score
            passed = expected_title_fragment.lower() in top_title.lower() and score > 0.30
            status = "✓ PASS" if passed else "✗ FAIL"
            print(f"  Query: '{query}'")
            print(f"    Top result: {top_title} (score: {score:.3f}) {status}")
            if not passed:
                all_pass = False
        else:
            print(f"  Query: '{query}' → ✗ FAIL (no results)")
            all_pass = False

    print(f"\nPhase 3 {'COMPLETE ✓' if all_pass else 'FAILED ✗ — check documents and embeddings'}")


if __name__ == "__main__":
    asyncio.run(embed())
