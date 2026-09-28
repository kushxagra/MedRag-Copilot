"""The /ask endpoint - the core RAG API."""

import logging

from fastapi import APIRouter

from app.core.monitoring import log_request
from app.models.schemas import AskRequest, AskResponse
from app.services.rag_pipeline import answer_question

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/ask", response_model=AskResponse)
def ask(request: AskRequest) -> AskResponse:
    logger.info("Received question: %s", request.question)
    result = answer_question(request.question, k=request.k)
    logger.info(
        "Answered in %d ms with %d sources, verdict=%s",
        result.latency_ms,
        len(result.sources),
        result.verification.get("verdict", "unknown"),
    )
    log_request(request.question, result)
    return AskResponse(
        answer=result.answer,
        sources=result.sources,
        verification=result.verification,
        latency_ms=result.latency_ms,
    )
