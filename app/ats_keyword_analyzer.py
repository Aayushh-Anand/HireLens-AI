
import re
from typing import Any

from app.jd_parser import parse_job_description


KEYWORD_ALIASES: dict[str, tuple[str, ...]] = {
    "Python": ("python",),
    "Java": ("java",),
    "JavaScript": ("javascript",),
    "TypeScript": ("typescript",),
    "SQL": ("sql",),
    "REST APIs": ("rest api", "rest apis", "restful api", "restful apis"),
    "FastAPI": ("fastapi",),
    "Flask": ("flask",),
    "Django": ("django",),
    "Node.js": ("node.js", "nodejs"),
    "React": ("react", "react.js", "reactjs"),
    "Next.js": ("next.js", "nextjs"),
    "Machine Learning": ("machine learning", "ml models"),
    "Deep Learning": ("deep learning",),
    "Generative AI": ("generative ai", "gen ai", "genai"),
    "Artificial Intelligence": ("artificial intelligence",),
    "Large Language Models": (
        "large language model",
        "large language models",
        "llm",
        "llms",
    ),
    "Natural Language Processing": (
        "natural language processing",
        "nlp",
    ),
    "Computer Vision": ("computer vision",),
    "Prompt Engineering": ("prompt engineering", "prompt design"),
    "RAG": (
        "retrieval augmented generation",
        "retrieval-augmented generation",
        "rag pipeline",
        "rag pipelines",
    ),
    "LLM APIs": (
        "llm api",
        "llm apis",
        "openai api",
        "anthropic api",
        "google gemini api",
    ),
    "LangChain": ("langchain",),
    "LlamaIndex": ("llamaindex", "llama index"),
    "Hugging Face": ("hugging face", "huggingface"),
    "TensorFlow": ("tensorflow",),
    "PyTorch": ("pytorch",),
    "scikit-learn": ("scikit-learn", "scikit learn", "sklearn"),
    "NumPy": ("numpy",),
    "pandas": ("pandas",),
    "Vector Databases": (
        "vector database",
        "vector databases",
        "vector db",
        "vector dbs",
    ),
    "Pinecone": ("pinecone",),
    "FAISS": ("faiss",),
    "ChromaDB": ("chromadb", "chroma db"),
    "Weaviate": ("weaviate",),
    "Embeddings": ("embeddings", "embedding models", "embedding"),
    "Semantic Search": ("semantic search",),
    "Cloud Platforms": ("cloud platforms", "cloud platform"),
    "AWS": ("aws", "amazon web services"),
    "Google Cloud": (
        "google cloud",
        "google cloud platform",
        "gcp",
    ),
    "Azure": ("azure", "microsoft azure"),
    "Docker": ("docker",),
    "Kubernetes": ("kubernetes",),
    "Git": ("git", "github"),
    "CI/CD": (
        "ci/cd",
        "continuous integration",
        "continuous delivery",
    ),
    "MongoDB": ("mongodb",),
    "PostgreSQL": ("postgresql", "postgres"),
    "MySQL": ("mysql",),
    "Redis": ("redis",),
    "Data Analysis": ("data analysis", "analyze data", "analyse data"),
    "Statistics": ("statistics", "statistical analysis"),
    "Model Evaluation": (
        "model evaluation",
        "evaluate models",
        "model metrics",
    ),
    "Fine-tuning": (
        "fine-tuning",
        "fine tuning",
        "fine-tune",
        "fine tune",
        "fine-tuned",
        "fine tuned",
    ),
    "API Integration": ("api integration", "integrate apis"),
    "Problem-solving": ("problem-solving", "problem solving"),
    "Communication": (
        "communication skills",
        "communicate effectively",
    ),
}

CONCEPT_ALIASES: dict[str, tuple[str, ...]] = {
    "Model deployment": (
        "deploy models",
        "model deployment",
        "deploy models in production",
    ),
    "Monitoring": (
        "monitor models",
        "model monitoring",
        "monitor in production",
    ),
    "Performance optimization": (
        "optimize performance",
        "performance optimization",
        "reduce latency",
    ),
    "AI agents": ("ai agents", "agentic ai"),
    "Chatbots": ("chatbot", "chatbots"),
    "Recommendation systems": (
        "recommendation system",
        "recommendation engine",
    ),
    "Data pipelines": ("data pipeline", "data pipelines"),
    "Security": ("security", "secure applications", "authentication"),
    "Testing": ("testing", "unit tests", "integration tests"),
}


def _normalize(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    text = re.sub(r"[ \t]+", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _term_pattern(term: str) -> re.Pattern:
    escaped = re.escape(term)
    escaped = escaped.replace(r"\ ", r"\s+")
    return re.compile(r"(?<!\w)" + escaped + r"(?!\w)", re.IGNORECASE)


def _find_occurrences(text: str, aliases: tuple[str, ...]) -> list[tuple[int, int, str]]:
    occurrences = []

    for alias in aliases:
        pattern = _term_pattern(alias)

        for match in pattern.finditer(text):
            occurrences.append((match.start(), match.end(), alias))

    return sorted(occurrences, key=lambda item: item[0])


def _make_evidence(text: str, aliases: tuple[str, ...]) -> str:
    """
    Evidence is intentionally searched in the supplied text only.
    The caller must pass the resume, never the job description.
    """
    occurrences = _find_occurrences(text, aliases)

    if not occurrences:
        return ""

    start_match, end_match, _ = occurrences[0]
    start = max(0, start_match - 85)
    end = min(len(text), end_match + 115)

    excerpt = re.sub(r"\s+", " ", text[start:end]).strip()

    if start > 0:
        excerpt = "…" + excerpt
    if end < len(text):
        excerpt += "…"

    return excerpt


def _extract_keywords(
    text: str,
    dictionary: dict[str, tuple[str, ...]],
) -> list[dict[str, Any]]:
    results = []

    for canonical, aliases in dictionary.items():
        found = [
            alias
            for alias in aliases
            if _term_pattern(alias).search(text)
        ]

        if found:
            results.append({
                "keyword": canonical,
                "matched_alias": found[0],
                "matched_aliases": found,
            })

    return results


def _keywords_from_sections(
    sections: dict[str, str],
    section_names: tuple[str, ...],
) -> list[dict[str, Any]]:
    text = "\n".join(
        sections.get(name, "")
        for name in section_names
        if sections.get(name)
    )
    return _extract_keywords(text, KEYWORD_ALIASES)


def analyze_keyword_coverage(
    resume_text: str,
    job_description: str,
) -> dict[str, Any]:
    """
    Compare curated JD keywords with resume text.
    Coverage is not a proprietary ATS score or hiring prediction.
    """
    resume = _normalize(resume_text)
    jd = _normalize(job_description)

    if not resume:
        raise ValueError("Resume text must not be empty.")

    if not jd:
        raise ValueError("Job description must not be empty.")

    parsed_jd = parse_job_description(jd)
    sections = parsed_jd["sections"]

    # Single source of truth for heading parsing.
    required_matches = _keywords_from_sections(
        sections,
        ("required_qualifications", "skills"),
    )
    preferred_matches = _keywords_from_sections(
        sections,
        ("preferred_qualifications",),
    )
    all_jd_matches = _extract_keywords(jd, KEYWORD_ALIASES)
    jd_concept_matches = _extract_keywords(jd, CONCEPT_ALIASES)

    # Resume matching is performed independently from JD matching.
    resume_matches = _extract_keywords(resume, KEYWORD_ALIASES)
    resume_concept_matches = _extract_keywords(resume, CONCEPT_ALIASES)

    required_names = {item["keyword"] for item in required_matches}
    preferred_names = {item["keyword"] for item in preferred_matches}
    jd_names = {item["keyword"] for item in all_jd_matches}
    resume_names = {item["keyword"] for item in resume_matches}
    jd_concepts = {item["keyword"] for item in jd_concept_matches}
    resume_concepts = {
        item["keyword"] for item in resume_concept_matches
    }

    required_matched = sorted(required_names & resume_names)
    required_missing = sorted(required_names - resume_names)
    preferred_matched = sorted(preferred_names & resume_names)
    preferred_missing = sorted(preferred_names - resume_names)
    matched_keywords = sorted(jd_names & resume_names)
    missing_keywords = sorted(jd_names - resume_names)
    matched_concepts = sorted(jd_concepts & resume_concepts)
    missing_concepts = sorted(jd_concepts - resume_concepts)

    coverage = (
        round(100 * len(matched_keywords) / len(jd_names))
        if jd_names
        else 0
    )

    # Critical fix: evidence excerpts come from resume text, not JD text.
    resume_evidence = {}

    for item in all_jd_matches:
        keyword = item["keyword"]

        if keyword not in resume_names:
            continue

        evidence = _make_evidence(
            resume,
            KEYWORD_ALIASES[keyword],
        )

        if evidence:
            resume_evidence[keyword] = evidence

    recommendations = []
    seen = set()

    def add_recommendation(
        keyword: str,
        priority: str,
        reason: str,
        advice: str,
    ) -> None:
        key = keyword.casefold()

        if key in seen:
            return

        seen.add(key)
        recommendations.append({
            "keyword": keyword,
            "priority": priority,
            "reason": reason,
            "advice": advice,
        })

    for keyword in required_missing:
        add_recommendation(
            keyword,
            "high",
            "Detected in required qualifications or skills but not detected in the resume.",
            "Include it only if you have genuine experience, training, or project evidence.",
        )

    for keyword in preferred_missing:
        if keyword not in required_names:
            add_recommendation(
                keyword,
                "medium",
                "Detected in the preferred-qualifications section but not in the resume.",
                "Include it only if supported by your actual experience.",
            )

    for keyword in missing_concepts:
        add_recommendation(
            keyword,
            "medium",
            "This job-related concept appears in the JD but was not detected in the resume.",
            "If you have relevant evidence, describe the project or task where you applied it.",
        )

    return {
        "analysis_type": "keyword_coverage",
        "coverage_percentage": coverage,
        "score_explanation": (
            "Keyword coverage is the percentage of curated job-description "
            "keywords detected in the resume text. It is not an ATS score, "
            "hiring probability, or a guarantee of compatibility."
        ),
        "job_description_sections": sections,
        "recognized_sections": parsed_jd["recognized_sections"],
        "required_keywords": sorted(required_names),
        "required_matched": required_matched,
        "required_missing": required_missing,
        "preferred_keywords": sorted(preferred_names),
        "preferred_matched": preferred_matched,
        "preferred_missing": preferred_missing,
        "all_jd_keywords": sorted(jd_names),
        "matched_keywords": matched_keywords,
        "missing_keywords": missing_keywords,
        "matched_concepts": matched_concepts,
        "missing_concepts": missing_concepts,
        "resume_keyword_evidence": resume_evidence,
        "recommended_keywords": recommendations[:30],
        "limitations": [
            "Keyword extraction uses a curated alias dictionary and may miss terms not included in it.",
            "Keyword presence does not prove proficiency; inspect the resume evidence.",
            "Required and preferred classification depends on the headings and wording in the job description.",
            "Keyword coverage is not a proprietary ATS score and does not predict hiring outcomes.",
        ],
    }
