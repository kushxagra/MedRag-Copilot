"""Split cleaned documents into overlapping chunks for embedding."""

import json
from pathlib import Path

from pipelines.clean_text import clean_text

RAW_DIR = Path("data/raw")
PROCESSED_PATH = Path("data/processed/chunks.jsonl")

CHUNK_SIZE_WORDS = 350
CHUNK_OVERLAP_WORDS = 50


def chunk_text(
    text: str, chunk_size: int = CHUNK_SIZE_WORDS, overlap: int = CHUNK_OVERLAP_WORDS
) -> list[str]:
    words = text.split()
    if len(words) <= chunk_size:
        return [text]

    chunks = []
    start = 0
    while start < len(words):
        end = start + chunk_size
        chunks.append(" ".join(words[start:end]))
        if end >= len(words):
            break
        start = end - overlap
    return chunks


def process_documents() -> None:
    PROCESSED_PATH.parent.mkdir(parents=True, exist_ok=True)

    raw_files = sorted(RAW_DIR.glob("pubmed_*.jsonl"))
    if not raw_files:
        print("No raw files found matching data/raw/pubmed_*.jsonl")
        return

    seen_chunks = set()
    total_docs = 0
    total_chunks = 0
    skipped_empty = 0
    skipped_duplicate = 0

    with PROCESSED_PATH.open("w", encoding="utf-8") as outfile:
        for raw_path in raw_files:
            file_docs = 0
            with raw_path.open("r", encoding="utf-8") as infile:
                for line in infile:
                    doc = json.loads(line)
                    total_docs += 1
                    file_docs += 1

                    cleaned = clean_text(doc.get("abstract", ""))
                    if not cleaned:
                        skipped_empty += 1
                        continue

                    for i, chunk in enumerate(chunk_text(cleaned)):
                        if not chunk.strip():
                            continue
                        if chunk in seen_chunks:
                            skipped_duplicate += 1
                            continue
                        seen_chunks.add(chunk)

                        record = {
                            "chunk_id": f"{doc['id']}-{i}",
                            "doc_id": doc["id"],
                            "source": doc["source"],
                            "title": doc["title"],
                            "url": doc["url"],
                            "chunk_index": i,
                            "text": chunk,
                        }
                        outfile.write(json.dumps(record) + "\n")
                        total_chunks += 1
            print(f"  {raw_path.name}: {file_docs} documents")

    print(
        f"Processed {total_docs} documents from {len(raw_files)} files -> {total_chunks} chunks"
    )
    print(
        f"Skipped {skipped_empty} empty documents, {skipped_duplicate} duplicate chunks"
    )
    print(f"Saved to {PROCESSED_PATH}")


if __name__ == "__main__":
    process_documents()
