"""Lightweight local request monitoring -- no external service required.

Appends one JSON record per /ask request to logs/requests.jsonl so
production usage patterns (latency, verdict distribution, retrieval
quality) can be analyzed later without a hosted MLOps platform.
"""

import json
from datetime import datetime, timezone
from pathlib import Path

LOG_DIR = Path("logs")
REQUESTS_LOG_PATH = LOG_DIR / "requests.jsonl"


def log_request(question: str, result) -> None:
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    top_score = result.sources[0]["score"] if result.sources else None
    record = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "question": question,
        "latency_ms": result.latency_ms,
        "num_sources": len(result.sources),
        "top_source_score": top_score,
        "verdict": result.verification.get("verdict", "unknown"),
        "num_unsupported_claims": len(
            result.verification.get("unsupported_claims", [])
        ),
    }
    with REQUESTS_LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record) + "\n")
