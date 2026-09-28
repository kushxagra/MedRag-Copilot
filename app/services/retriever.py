"""Semantic retrieval over the indexed medical document chunks."""

from dataclasses import dataclass

import chromadb
from sentence_transformers import SentenceTransformer

from app.core.config import settings

EMBEDDING_MODEL_NAME = "all-MiniLM-L6-v2"
COLLECTION_NAME = "medrag_chunks"


@dataclass
class RetrievedChunk:
    chunk_id: str
    text: str
    title: str
    url: str
    score: float


class Retriever:
    """Wraps embedding + vector search behind retrieve(). Pass a custom
    db_path to point at an isolated store (e.g. in tests); defaults to the
    configured production vector store otherwise."""

    def __init__(
        self, db_path: str | None = None, collection_name: str = COLLECTION_NAME
    ):
        self._db_path = db_path or settings.vector_db_path
        self._collection_name = collection_name
        self._model: SentenceTransformer | None = None
        self._collection = None

    def _get_model(self) -> SentenceTransformer:
        if self._model is None:
            self._model = SentenceTransformer(EMBEDDING_MODEL_NAME)
        return self._model

    def _get_collection(self):
        if self._collection is None:
            client = chromadb.PersistentClient(path=self._db_path)
            self._collection = client.get_or_create_collection(self._collection_name)
        return self._collection

    def index(self, ids: list[str], texts: list[str], metadatas: list[dict]) -> None:
        embeddings = self._get_model().encode(texts).tolist()
        self._get_collection().upsert(
            ids=ids, embeddings=embeddings, documents=texts, metadatas=metadatas
        )

    def retrieve(self, query: str, k: int = 5) -> list[RetrievedChunk]:
        model = self._get_model()
        collection = self._get_collection()

        query_embedding = model.encode([query]).tolist()
        results = collection.query(query_embeddings=query_embedding, n_results=k)

        chunks = []
        for i in range(len(results["ids"][0])):
            metadata = results["metadatas"][0][i]
            chunks.append(
                RetrievedChunk(
                    chunk_id=results["ids"][0][i],
                    text=results["documents"][0][i],
                    title=metadata["title"],
                    url=metadata["url"],
                    score=1 - results["distances"][0][i],
                )
            )
        return chunks


default_retriever = Retriever()


def retrieve(query: str, k: int = 5) -> list[RetrievedChunk]:
    """Convenience wrapper around the default production retriever."""
    return default_retriever.retrieve(query, k=k)
