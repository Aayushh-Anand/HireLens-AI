
import json
import re
import time
from pathlib import Path

DATA_PATH = Path("data/benchmark_samples.json")
REPORT_PATH = Path("data/benchmark_results.json")


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-zA-Z0-9+#.]+", text.lower()))


def keyword_similarity(first: str, second: str) -> float:
    """Jaccard token overlap: a simple, non-semantic baseline."""
    tokens_a = tokenize(first)
    tokens_b = tokenize(second)

    if not tokens_a or not tokens_b:
        return 0.0

    return len(tokens_a & tokens_b) / len(tokens_a | tokens_b)


def evaluate_scorer(samples: list[dict], scorer, model_name: str) -> dict:
    correct = 0
    margins = []
    start = time.perf_counter()

    for sample in samples:
        requirement = sample["requirement"]

        positive_score = scorer(
            requirement, sample["positive_evidence"]
        )
        negative_score = scorer(
            requirement, sample["negative_evidence"]
        )

        margin = positive_score - negative_score
        margins.append(margin)

        if margin > 0:
            correct += 1

    elapsed = time.perf_counter() - start
    count = len(samples)

    return {
        "model": model_name,
        "examples": count,
        "pairwise_accuracy": round(correct / count, 4) if count else None,
        "average_score_margin": (
            round(sum(margins) / count, 4) if count else None
        ),
        "evaluation_seconds": round(elapsed, 4),
    }


def main():
    if not DATA_PATH.exists():
        raise FileNotFoundError(
            f"Benchmark dataset not found: {DATA_PATH}"
        )

    samples = json.loads(DATA_PATH.read_text(encoding="utf-8"))

    if not samples:
        raise ValueError("Benchmark dataset is empty.")

    baseline = evaluate_scorer(
        samples,
        keyword_similarity,
        "keyword_jaccard",
    )

    results = [baseline]

    # Model evaluation is optional until sentence-transformers is installed.
    try:
        from sentence_transformers import SentenceTransformer
        from sentence_transformers.util import cos_sim
    except ImportError:
        print(
            "sentence-transformers is not installed. "
            "Only the keyword baseline will run."
        )
    else:
        model_names = [
            "sentence-transformers/all-MiniLM-L6-v2",
            "sentence-transformers/all-mpnet-base-v2",
        ]

        for model_name in model_names:
            print(f"Loading model: {model_name}")
            try:
                model = SentenceTransformer(model_name, device="cpu")

                def semantic_similarity(first, second, current_model=model):
                    embeddings = current_model.encode(
                        [first, second],
                        convert_to_tensor=True,
                        normalize_embeddings=True,
                    )
                    return float(cos_sim(embeddings[0], embeddings[1]).item())

                result = evaluate_scorer(
                    samples,
                    semantic_similarity,
                    model_name,
                )
                results.append(result)

                del model
            except Exception as exc:
                results.append({
                    "model": model_name,
                    "error": f"{type(exc).__name__}: {exc}",
                })

    REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
    REPORT_PATH.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\nBenchmark results:")
    print(json.dumps(results, indent=2))
    print(f"\nSaved report to: {REPORT_PATH}")


if __name__ == "__main__":
    main()
