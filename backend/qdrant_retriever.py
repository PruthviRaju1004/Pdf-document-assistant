import hashlib
import uuid

from sentence_transformers import SentenceTransformer
from qdrant_client import QdrantClient
from qdrant_client.models import (
    VectorParams,
    Distance,
    PointStruct,
    Filter,
    FieldCondition,
    MatchValue,
)
from .pdf_chunker import PageChunk, chunk_pages

# Deterministic id for the sentinel point that stores a hash of the chunk
# content a collection was built from, so we can tell when a repo's README
# has changed upstream and the cached embeddings need refreshing.
_META_ID = str(uuid.uuid5(uuid.NAMESPACE_URL, "doc-assistant/content-hash-meta"))
_META_FILTER = Filter(must_not=[FieldCondition(key="__meta__", match=MatchValue(value=True))])


def _content_hash(chunks: list[PageChunk]) -> str:
    joined = "\x1f".join(f"{c.page_number}\x1e{c.text}" for c in chunks)
    return hashlib.sha256(joined.encode("utf-8")).hexdigest()


class QdrantRetriever:
    def __init__(self, chunks, collection_name: str):
        self.chunks = chunks
        self.model = SentenceTransformer("all-MiniLM-L6-v2")
        self.client = QdrantClient(url="http://localhost:6333")
        self.collection_name = collection_name
        content_hash = _content_hash(chunks)

        if not self.client.collection_exists(self.collection_name):
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )
        else:
            existing = self.client.retrieve(self.collection_name, ids=[_META_ID])
            if existing and existing[0].payload.get("content_hash") == content_hash:
                print(f"Collection '{self.collection_name}' is up to date — skipping re-embedding.")
                return
            print(f"Collection '{self.collection_name}' is stale (README changed) — re-embedding.")
            self.client.delete_collection(self.collection_name)
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=VectorParams(size=384, distance=Distance.COSINE),
            )

        texts = [c.text for c in chunks]
        vectors = self.model.encode(texts)
        points = [
            PointStruct(
                id=i,
                vector=vector.tolist(),
                payload={
                    "chunk_id": chunk.chunk_id,
                    "page_number": chunk.page_number,
                    "text": chunk.text,
                },
            )
            for i, (chunk, vector) in enumerate(zip(chunks, vectors))
        ]
        # Sentinel point recording what content this collection was built
        # from, so the next call can detect staleness without re-embedding.
        points.append(
            PointStruct(
                id=_META_ID,
                vector=[0.0] * 384,
                payload={"__meta__": True, "content_hash": content_hash},
            )
        )
        self.client.upsert(collection_name=self.collection_name, points=points)

    def search(self, query: str, top_k: int = 3, min_score: float = 0.0):
        query_vector = self.model.encode([query])[0]

        response = self.client.query_points(
            collection_name=self.collection_name,
            query=query_vector.tolist(),
            query_filter=_META_FILTER,
            limit=top_k,
            score_threshold=min_score if min_score > 0 else None,
        )
        results = []
        for point in response.points:
            chunk = PageChunk(
                chunk_id=point.payload["chunk_id"],
                page_number=point.payload["page_number"],
                text=point.payload["text"],
            )
            results.append((chunk, point.score))
        return results


if __name__ == "__main__":
    from .pdf_extractor import PageText

    # Scenario A: first-ever run on this content
    pages_v1 = [
        PageText(page_number=1, text="Flask is lightweight."),
        PageText(page_number=2, text="Install with pip: pip install flask"),
    ]
    chunks_v1 = chunk_pages(pages_v1)

    print("--- Scenario A: first run, fresh collection ---")
    retriever_a = QdrantRetriever(chunks_v1, collection_name="staleness_test")
    print(f"Stored {len(chunks_v1)} real chunks (plus 1 sentinel)")

    # Scenario B: same content, run again -- should skip re-embedding
    print("\n--- Scenario B: same content, second run ---")
    retriever_b = QdrantRetriever(chunks_v1, collection_name="staleness_test")

    # Scenario C: content changed -- should detect staleness and re-embed
    pages_v2 = [
        PageText(page_number=1, text="Flask is lightweight."),
        PageText(page_number=2, text="Install with pip: pip install flask THIS TEXT CHANGED"),
    ]
    chunks_v2 = chunk_pages(pages_v2)

    print("\n--- Scenario C: content changed, third run ---")
    retriever_c = QdrantRetriever(chunks_v2, collection_name="staleness_test")

    # Scenario D: confirm search results never include the sentinel point
    print("\n--- Scenario D: search results should exclude sentinel ---")
    results = retriever_c.search("how do I install this", top_k=5, min_score=0.0)
    print(f"Got {len(results)} results")
    for chunk, score in results:
        print(f"  page {chunk.page_number}, score={score:.3f}: {chunk.text[:50]!r}")