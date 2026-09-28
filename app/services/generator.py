"""LLM answer generation grounded in retrieved context."""

import ollama

from app.core.config import settings

SYSTEM_PROMPT = """You are a careful medical literature assistant. Answer the \
user's question using ONLY the information in the provided context passages.

Before answering, check whether the context passages actually address the \
SPECIFIC question asked - not just the same general medical topic or condition. \
If the context only discusses a related but different aspect of the condition \
(for example, the question asks about symptoms but the context is about a \
comorbidity, treatment adherence, or an unrelated biomarker), you must say \
explicitly that the retrieved context does not directly address the question, \
rather than answering the related-but-different topic as if it were relevant.

Do not use any outside knowledge. Keep your answer concise and clinically \
precise."""


def build_prompt(question: str, context_chunks: list[str]) -> str:
    context_block = "\n\n".join(
        f"[Source {i+1}]\n{chunk}" for i, chunk in enumerate(context_chunks)
    )
    return (
        f"Context passages:\n{context_block}\n\n"
        f"Question: {question}\n\n"
        "First check: do these passages actually address this specific question? "
        "If not, say so plainly. If yes, answer using only the context above, "
        "and reference sources like [Source 1] where relevant."
    )


def generate_answer(question: str, context_chunks: list[str]) -> str:
    prompt = build_prompt(question, context_chunks)

    response = ollama.chat(
        model=settings.llm_model_name,
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt},
        ],
    )
    return response["message"]["content"]
