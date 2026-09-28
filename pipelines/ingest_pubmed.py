"""Fetch PubMed abstracts for a given search topic and save them as JSONL."""

import json
import re
import time
from pathlib import Path

from Bio import Entrez

from app.core.config import settings

Entrez.email = "kdwivedi1405@gmail.com"  # NCBI requires a real contact email
Entrez.api_key = settings.ncbi_api_key or None

RAW_DIR = Path("data/raw")


def slugify(text: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "_", text.lower()).strip("_")
    return slug or "topic"


def search_pubmed(query: str, max_results: int = 200) -> list[str]:
    handle = Entrez.esearch(db="pubmed", term=query, retmax=max_results)
    record = Entrez.read(handle)
    handle.close()
    return record["IdList"]


def fetch_abstracts(pubmed_ids: list[str]) -> list[dict]:
    records = []
    batch_size = 50
    for i in range(0, len(pubmed_ids), batch_size):
        batch = pubmed_ids[i : i + batch_size]
        handle = Entrez.efetch(db="pubmed", id=batch, rettype="abstract", retmode="xml")
        data = Entrez.read(handle)
        handle.close()

        for article in data.get("PubmedArticle", []):
            try:
                medline = article["MedlineCitation"]
                article_data = medline["Article"]
                title = str(article_data.get("ArticleTitle", ""))
                abstract_parts = article_data.get("Abstract", {}).get(
                    "AbstractText", []
                )
                abstract = " ".join(str(p) for p in abstract_parts)
                pmid = str(medline["PMID"])
                if not abstract:
                    continue
                records.append(
                    {
                        "id": pmid,
                        "source": "pubmed",
                        "title": title,
                        "abstract": abstract,
                        "url": f"https://pubmed.ncbi.nlm.nih.gov/{pmid}/",
                    }
                )
            except (KeyError, IndexError):
                continue

        time.sleep(0.34)

    return records


def main(query: str, max_results: int = 200) -> None:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    output_path = RAW_DIR / f"pubmed_{slugify(query)}.jsonl"

    ids = search_pubmed(query, max_results)
    print(f"Found {len(ids)} PubMed IDs for query: {query!r}")

    records = fetch_abstracts(ids)
    print(f"Fetched {len(records)} abstracts with usable text")

    with output_path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record) + "\n")

    print(f"Saved to {output_path}")


if __name__ == "__main__":
    import sys

    topic = sys.argv[1] if len(sys.argv) > 1 else "hypertension treatment guidelines"
    main(topic)
