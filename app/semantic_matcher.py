
"""Optional semantic matching for HireLens AI.

Semantic results are suggestions only. They never count as confirmed
skills or change the existing compatibility score.
"""

import logging
import re
from functools import lru_cache
from typing import Any

from sentence_transformers import SentenceTransformer, util

logger = logging.getLogger(__name__)

MODEL_NAME = "sentence-transformers/all-MiniLM-L6-v2"


@lru_cache(maxsize=1)
def _load_model() -> Any:
    """Load the CPU model once and reuse it."""
    return SentenceTransformer(MODEL_NAME, device="cpu")


def _normalize_text(text: str) -> str:
    """Normalize whitespace and invisible PDF extraction characters."""
    text = (
        text.replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
    )
    return re.sub(r"\s+", " ", text).strip()


def _split_sentences(text: str) -> list[str]:
    """Split text into unique, useful evidence units."""
    if not isinstance(text, str) or not text.strip():
        return []

    text = _normalize_text(text)

    heading_only_patterns = [
        r"skills",
        r"technical skills",
        r"languages",
        r"frontend",
        r"backend",
        r"backend\s*(?:&|and)\s*apis",
        r"ai\s*(?:&|and)\s*machine learning",
        r"databases",
        r"devops\s*&\s*tools",
        r"education",
    ]

    parts = re.split(r"(?<=[.!?])\s+|\n+", text)
    results = []
    seen = set()

    for part in parts:
        sentence = _normalize_text(part.strip(" \t-*•:"))

        if len(sentence) < 15:
            continue

        normalized = sentence.casefold()

        if any(
            re.fullmatch(pattern, normalized, re.IGNORECASE)
            for pattern in heading_only_patterns
        ):
            continue

        if normalized in seen:
            continue

        seen.add(normalized)
        results.append(sentence)

    return results


def find_semantic_suggestions(
    resume_text: str,
    requirement_text: str,
    threshold: float = 0.55,
    top_k: int = 3,
    one_per_requirement: bool = False,
) -> list[dict]:
    """Find relevant resume evidence for each JD requirement.

    Results are suggestions, not proof of proficiency. They do not
    alter the rule-based compatibility score.

    Set one_per_requirement=True to return only the best evidence
    item for each requirement.
    """
    if not 0.0 <= threshold <= 1.0:
        raise ValueError("threshold must be between 0 and 1")

    if top_k < 1:
        raise ValueError("top_k must be at least 1")

    if not isinstance(resume_text, str):
        raise TypeError("resume_text must be a string")

    if not isinstance(requirement_text, str):
        raise TypeError("requirement_text must be a string")

    resume_sentences = _split_sentences(resume_text)
    requirement_sentences = _split_sentences(requirement_text)

    if not resume_sentences or not requirement_sentences:
        return []

    try:
        model = _load_model()

        resume_embeddings = model.encode(
            resume_sentences,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )
        requirement_embeddings = model.encode(
            requirement_sentences,
            convert_to_tensor=True,
            normalize_embeddings=True,
        )

        similarities = util.cos_sim(
            requirement_embeddings,
            resume_embeddings,
        )

        suggestions = []
        seen_pairs = set()

        for index, requirement in enumerate(requirement_sentences):
            scores = similarities[index]
            best_indices = scores.argsort(descending=True)

            requirement_results = []

            for resume_index in best_indices:
                resume_index = int(resume_index)
                similarity = float(scores[resume_index].item())

                if similarity < threshold:
                    break

                evidence = resume_sentences[resume_index]
                pair_key = (
                    requirement.casefold(),
                    evidence.casefold(),
                )

                if pair_key in seen_pairs:
                    continue

                seen_pairs.add(pair_key)

                requirement_results.append(
                    {
                        "requirement": requirement,
                        "resume_evidence": evidence,
                        "similarity": round(similarity, 4),
                        "status": "semantic_suggestion",
                        "counts_as_confirmed_match": False,
                    }
                )

                if one_per_requirement:
                    break

                if len(requirement_results) >= top_k:
                    break

            suggestions.extend(requirement_results)

        suggestions.sort(
            key=lambda item: (
                -item["similarity"],
                item["requirement"].casefold(),
                item["resume_evidence"].casefold(),
            )
        )

        return suggestions

    except Exception:
        logger.exception("Semantic matching failed.")
        return []
