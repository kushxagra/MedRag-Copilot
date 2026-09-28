"""End-to-end RAG orchestration: retrieve -> generate -> verify -> return with sources."""

import time
from dataclasses import dataclass, field

from app.services.generator import generate_answer
from app.services.retriever import retrieve
from app.services.verifier import verify_answer


@dataclass
class RagResult:
    answer: str
    sources: list[dict]
    contexts: list[str]
    verification: dict = field(default_factory=dict)
    latency_ms: int = 0


def answer_question(question: str, k: int = 5) -> RagResult:
    start = time.perf_counter()

    retrieved = retrieve(question, k=k)
    context_chunks = [c.text for c in retrieved]

    answer = generate_answer(question, context_chunks)

    verification = verify_answer(question, context_chunks, answer)

    latency_ms = int((time.perf_counter() - start) * 1000)

    sources = [
        {"title": c.title, "url": c.url, "score": round(c.score, 3)} for c in retrieved
    ]

    return RagResult(
        answer=answer,
        sources=sources,
        contexts=context_chunks,
        verification=verification,
        latency_ms=latency_ms,
    )
