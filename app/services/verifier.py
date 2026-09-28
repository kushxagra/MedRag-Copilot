"""Self-verification layer: checks a generated answer against retrieved evidence."""

import json
import logging

import ollama

from app.core.config import settings

logger = logging.getLogger(__name__)

VERIFICATION_PROMPT = """You are a strict medical fact-checker. You will be given a QUESTION, the CONTEXT passages that were retrieved to answer it, and an ANSWER that was generated from that context.

Check TWO things, in order:
1. RELEVANCE: Does the ANSWER actually address the SPECIFIC question asked - not just the same general topic or condition? An answer that discusses a related but different aspect (e.g. a comorbidity, when symptoms were asked about) does NOT count as relevant.
2. GROUNDING: If the answer is relevant, is it actually supported by the CONTEXT? Do not use outside knowledge - only judge based on what is written in the CONTEXT.

Respond with ONLY a JSON object in this exact format, no other text:
{{
  "addresses_question": true | false,
  "verdict": "supported" | "partially_supported" | "unsupported" | "off_topic",
  "unsupported_claims": ["list of specific claims in the answer that are NOT backed by the context, empty list if none"],
  "explanation": "one sentence explaining your verdict"
}}

If addresses_question is false, verdict must be "off_topic" regardless of grounding.

QUESTION:
{question}

CONTEXT:
{context}

ANSWER:
{answer}

JSON response:"""


def verify_answer(question: str, context_chunks: list[str], answer: str) -> dict:
    context = "\n\n".join(f"[{i + 1}] {c}" for i, c in enumerate(context_chunks))
    prompt = VERIFICATION_PROMPT.format(
        question=question, context=context, answer=answer
    )

    response = ollama.chat(
        model=settings.verifier_model_name,
        messages=[{"role": "user", "content": prompt}],
        options={"temperature": 0},
    )
    raw = response["message"]["content"].strip()

    try:
        cleaned = raw
        if cleaned.startswith("```"):
            cleaned = cleaned.strip("`")
            if cleaned.startswith("json"):
                cleaned = cleaned[4:]
        result = json.loads(cleaned.strip())
    except json.JSONDecodeError:
        logger.warning("Verification step returned non-JSON output: %s", raw[:200])
        result = {
            "addresses_question": None,
            "verdict": "unverified",
            "unsupported_claims": [],
            "explanation": "Verification step failed to produce a parseable result.",
        }

    return result
