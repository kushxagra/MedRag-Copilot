"""Embed processed chunks and index them into a persistent Chroma vector store."""

import json
from pathlib import Path

from app.services.retriever import Retriever

CHUNKS_PATH = Path("data/processed/chunks.jsonl")


def load_chunks() -> list[dict]:
    chunks = []
    with CHUNKS_PATH.open("r", encoding="utf-8") as f:
        for line in f:
            chunks.append(json.loads(line))
    return chunks


def build_index() -> None:
    chunks = load_chunks()
    print(f"Loaded {len(chunks)} chunks to index")

    retriever = Retriever()
    retriever.index(
        ids=[c["chunk_id"] for c in chunks],
        texts=[c["text"] for c in chunks],
        metadatas=[
            {
                "doc_id": c["doc_id"],
                "title": c["title"],
                "source": c["source"],
                "url": c["url"],
            }
            for c in chunks
        ],
    )

    print(f"Indexed {len(chunks)} chunks")


if __name__ == "__main__":
    build_index()
