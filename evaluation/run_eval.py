"""Evaluate the RAG pipeline using RAGAS metrics, judged by the local Ollama model."""

import json
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain_ollama import ChatOllama
from ragas import EvaluationDataset, RunConfig, evaluate
from ragas.embeddings import LangchainEmbeddingsWrapper
from ragas.llms import LangchainLLMWrapper
from ragas.metrics import AnswerRelevancy, ContextPrecision, ContextRecall, Faithfulness

from app.core.config import settings
from app.services.rag_pipeline import answer_question

TEST_QUESTIONS_PATH = Path("evaluation/test_questions.json")
RESULTS_PATH = Path("evaluation/results.json")
EVAL_HISTORY_PATH = Path("evaluation/eval_history.jsonl")


def build_dataset() -> EvaluationDataset:
    with TEST_QUESTIONS_PATH.open("r", encoding="utf-8") as f:
        test_cases = json.load(f)

    samples = []
    for i, case in enumerate(test_cases, start=1):
        question = case["question"]
        reference = case.get("reference", "")

        print(f"[{i}/{len(test_cases)}] Running: {question}")
        result = answer_question(question)

        samples.append(
            {
                "user_input": question,
                "response": result.answer,
                "retrieved_contexts": result.contexts,
                "reference": reference,
            }
        )

    return EvaluationDataset.from_list(samples)


def main() -> None:
    dataset = build_dataset()

    judge_llm = LangchainLLMWrapper(ChatOllama(model=settings.llm_model_name))
    judge_embeddings = LangchainEmbeddingsWrapper(
        HuggingFaceEmbeddings(model_name="sentence-transformers/all-MiniLM-L6-v2")
    )

    print(
        "\nRunning RAGAS evaluation (this calls the local LLM many times, be patient)..."
    )
    result = evaluate(
        dataset=dataset,
        metrics=[
            Faithfulness(),
            AnswerRelevancy(),
            ContextPrecision(),
            ContextRecall(),
        ],
        llm=judge_llm,
        embeddings=judge_embeddings,
        run_config=RunConfig(timeout=300, max_workers=1),
    )

    print("\n=== RAGAS Evaluation Results ===")
    print(result)

    df = result.to_pandas()
    df.to_json(RESULTS_PATH, orient="records", indent=2)
    print(f"\nSaved detailed per-question results to {RESULTS_PATH}")

    metric_cols = [
        "faithfulness",
        "answer_relevancy",
        "context_precision",
        "context_recall",
    ]
    aggregate = {}
    for col in metric_cols:
        if col in df.columns:
            mean_val = df[col].mean(skipna=True)
            aggregate[col] = None if pd.isna(mean_val) else round(float(mean_val), 4)
        else:
            aggregate[col] = None

    history_entry = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "generator_model": settings.llm_model_name,
        "judge_model": settings.llm_model_name,
        "num_questions": len(df),
        "metrics": aggregate,
    }
    EVAL_HISTORY_PATH.parent.mkdir(parents=True, exist_ok=True)
    with EVAL_HISTORY_PATH.open("a", encoding="utf-8") as f:
        f.write(json.dumps(history_entry) + "\n")
    print(f"Appended run summary to {EVAL_HISTORY_PATH}")


if __name__ == "__main__":
    main()
