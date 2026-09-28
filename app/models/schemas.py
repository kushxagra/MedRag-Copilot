from pydantic import BaseModel


class AskRequest(BaseModel):
    question: str
    k: int = 5


class SourceItem(BaseModel):
    title: str
    url: str
    score: float


class VerificationResult(BaseModel):
    verdict: str
    unsupported_claims: list[str] = []
    explanation: str = ""


class AskResponse(BaseModel):
    answer: str
    sources: list[SourceItem]
    verification: VerificationResult
    latency_ms: int
