from app.ats_keyword_analyzer import analyze_keyword_coverage
from app.jd_parser import parse_job_description


def test_preferred_candidate_profile_is_not_lost():
    jd = (
        "Role overview: Build AI products. "
        "Responsibilities: Develop AI applications. "
        "Preferred candidate profile: "
        "Strong programming skills in Python. "
        "Knowledge of SQL and Docker. "
        "Nice to have Kubernetes experience."
    )

    result = parse_job_description(jd)
    sections = result["sections"]

    assert "overview" in sections
    assert "responsibilities" in sections
    assert "required_qualifications" in sections
    assert "preferred_qualifications" in sections

    assert "Python" in sections["required_qualifications"]
    assert "SQL" in sections["required_qualifications"]
    assert "Docker" in sections["required_qualifications"]
    assert "Kubernetes" in sections["preferred_qualifications"]


def test_keyword_evidence_never_copies_job_description():
    resume = (
        "Coco Zhang\n"
        "Education: Machine Learning course.\n"
        "Skills: Python, GCP, LLMs.\n"
        "Projects: Built a RAG pipeline using Python."
    )
    jd = (
        "Overview: We build AI products for businesses.\n"
        "Responsibilities: Build large language model applications.\n"
        "Required Qualifications: Python, GCP, LLMs, Docker."
    )

    result = analyze_keyword_coverage(resume, jd)
    evidence = result["resume_keyword_evidence"]

    assert evidence["Python"]
    assert evidence["Google Cloud"]
    assert evidence["Large Language Models"]

    for excerpt in evidence.values():
        assert excerpt
        assert "We build AI products for businesses" not in excerpt
        assert "Responsibilities:" not in excerpt
        excerpt.startswith("…") and excerpt.endswith("…")

    assert "Docker" not in evidence


def test_required_and_preferred_keyword_lists_are_separate():
    resume = "Python and Docker developer"
    jd = (
        "Required Qualifications: Python and FastAPI.\n"
        "Preferred Qualifications: Docker and Kubernetes."
    )

    result = analyze_keyword_coverage(resume, jd)

    assert "FastAPI" in result["required_missing"]
    assert "Docker" in result["preferred_matched"]
    assert "Kubernetes" in result["preferred_missing"]


def test_inline_headings_are_split_into_correct_sections():
    result = parse_job_description(
        "Overview: Build products. "
        "Responsibilities: Develop APIs. "
        "Required Qualifications: Python and SQL. "
        "Preferred Qualifications: Kubernetes."
    )

    sections = result["sections"]

    assert sections["overview"] == "Build products."
    assert sections["responsibilities"] == "Develop APIs."
    assert "Python" in sections["required_qualifications"]
    assert "SQL" in sections["required_qualifications"]
    assert sections["preferred_qualifications"] == "Kubernetes."


def test_keyword_evidence_uses_resume_aliases():
    resume = (
        "Worked with LLMs and deployed an application on GCP."
    )
    jd = (
        "Required Qualifications: "
        "Large Language Models and Google Cloud experience."
    )

    result = analyze_keyword_coverage(resume, jd)
    evidence = result["resume_keyword_evidence"]

    assert "Large Language Models" in evidence
    assert "Google Cloud" in evidence
    assert "LLMs" in evidence["Large Language Models"]
    assert "GCP" in evidence["Google Cloud"]


def test_coverage_is_not_reported_as_ats_score():
    result = analyze_keyword_coverage(
        "Python developer",
        "Required Qualifications: Python and Docker.",
    )

    assert "coverage_percentage" in result
    assert "ats_score" not in result
    assert "not an ATS score" in result["score_explanation"]
