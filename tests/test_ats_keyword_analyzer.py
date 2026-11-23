
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from app.ats_keyword_analyzer import analyze_keyword_coverage
from app.main import app


client = TestClient(app)


def test_keyword_analysis_returns_expected_fields():
    result = analyze_keyword_coverage(
        "Python, FastAPI, SQL, and REST APIs",
        (
            "Responsibilities:\n"
            "Build REST APIs using Python.\n"
            "Required Qualifications:\n"
            "Python, FastAPI, SQL, and Docker experience required."
        ),
    )

    expected = {
        "analysis_type",
        "coverage_percentage",
        "score_explanation",
        "job_description_sections",
        "recognized_sections",
        "required_keywords",
        "required_matched",
        "required_missing",
        "preferred_keywords",
        "preferred_matched",
        "preferred_missing",
        "all_jd_keywords",
        "matched_keywords",
        "missing_keywords",
        "matched_concepts",
        "missing_concepts",
        "resume_keyword_evidence",
        "recommended_keywords",
        "limitations",
    }

    assert expected.issubset(result.keys())


def test_keywords_are_matched_and_missing_terms_identified():
    result = analyze_keyword_coverage(
        "Python, SQL, REST APIs",
        (
            "Required Qualifications:\n"
            "Python, SQL, FastAPI and Docker experience required."
        ),
    )

    assert "Python" in result["matched_keywords"]
    assert "SQL" in result["matched_keywords"]
    assert "FastAPI" in result["missing_keywords"]
    assert "Docker" in result["missing_keywords"]


def test_required_and_preferred_sections_are_separated():
    result = analyze_keyword_coverage(
        "Python and Docker",
        (
            "Required Qualifications:\n"
            "Python and FastAPI experience.\n"
            "Preferred Qualifications:\n"
            "Docker and Kubernetes."
        ),
    )

    assert "required_qualifications" in result["recognized_sections"]
    assert "preferred_qualifications" in result["recognized_sections"]

    assert "FastAPI" in result["required_missing"]
    assert "Docker" in result["preferred_matched"]
    assert "Kubernetes" in result["preferred_missing"]


def test_preferred_candidate_profile_does_not_make_every_item_preferred():
    result = analyze_keyword_coverage(
        "Python and SQL",
        (
            "Role overview:\n"
            "Build AI products for customers.\n"
            "Preferred candidate profile:\n"
            "Strong programming skills in Python.\n"
            "Knowledge of SQL and Docker.\n"
            "Nice to have Kubernetes experience."
        ),
    )

    assert "Python" in result["required_matched"]
    assert "SQL" in result["required_matched"]
    assert "Docker" in result["required_missing"]
    assert "Kubernetes" in result["preferred_missing"]


def test_inline_headings_are_detected():
    result = analyze_keyword_coverage(
        "Python and FastAPI",
        (
            "Overview: Build backend products. "
            "Responsibilities: Develop REST APIs. "
            "Required Qualifications: Python and Docker. "
            "Preferred Qualifications: Kubernetes."
        ),
    )

    sections = result["job_description_sections"]

    assert "overview" in sections
    assert "responsibilities" in sections
    assert "required_qualifications" in sections
    assert "preferred_qualifications" in sections
    assert "Docker" in result["required_missing"]
    assert "Kubernetes" in result["preferred_missing"]


def test_keyword_matching_respects_word_boundaries():
    result = analyze_keyword_coverage(
        "JavaScript developer",
        "Required Qualifications:\nJava experience required.",
    )

    assert "Java" in result["missing_keywords"]


def test_keyword_coverage_stays_within_range():
    result = analyze_keyword_coverage(
        "Python, FastAPI, SQL",
        "Required Skills:\nPython, FastAPI, SQL, Docker.",
    )

    assert 0 <= result["coverage_percentage"] <= 100


def test_recommendations_include_only_missing_detected_terms():
    result = analyze_keyword_coverage(
        "Python developer",
        "Required Qualifications:\nPython, FastAPI, Docker.",
    )

    recommended = {
        item["keyword"]
        for item in result["recommended_keywords"]
    }

    assert "FastAPI" in recommended
    assert "Docker" in recommended
    assert "Python" not in recommended


def test_evidence_uses_any_resume_alias_not_only_jd_alias():
    result = analyze_keyword_coverage(
        (
            "Completed training in Large Language Model fundamentals "
            "with Google Cloud and Simplilearn."
        ),
        (
            "Required Qualifications:\n"
            "Experience with LLMs and GCP."
        ),
    )

    evidence = result["resume_keyword_evidence"]

    assert "Large Language Models" in evidence
    assert "Google Cloud" in evidence
    assert evidence["Large Language Models"]
    assert evidence["Google Cloud"]


def test_evidence_is_returned_for_detected_keywords():
    result = analyze_keyword_coverage(
        "I developed APIs using Python and FastAPI.",
        "Required Qualifications:\nPython and FastAPI experience.",
    )

    assert result["resume_keyword_evidence"]["Python"]
    assert result["resume_keyword_evidence"]["FastAPI"]


def test_empty_resume_is_rejected():
    try:
        analyze_keyword_coverage(
            " ",
            "Python developer with API experience.",
        )
        assert False, "Expected ValueError for empty resume"
    except ValueError:
        pass


def test_empty_job_description_is_rejected():
    try:
        analyze_keyword_coverage("Python developer", " ")
        assert False, "Expected ValueError for empty JD"
    except ValueError:
        pass


def make_docx() -> bytes:
    document = Document()
    document.add_heading("Software Engineer Resume", level=1)
    document.add_paragraph("alex@example.com")
    document.add_heading("Technical Skills", level=2)
    document.add_paragraph("Python, FastAPI, SQL, REST APIs")
    document.add_heading("Projects", level=2)
    document.add_paragraph(
        "Developed a Python API using FastAPI and SQL."
    )
    document.add_heading("Education", level=2)
    document.add_paragraph("Bachelor of Technology, 2022-2026")

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


def test_analyze_api_includes_keyword_analysis():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.docx",
                make_docx(),
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
            )
        },
        data={
            "job_description": (
                "Responsibilities:\n"
                "Build REST APIs using Python.\n"
                "Required Qualifications:\n"
                "Python, FastAPI, SQL and Docker experience required.\n"
                "Preferred Qualifications:\n"
                "Kubernetes experience is preferred."
            )
        },
    )

    assert response.status_code == 200

    body = response.json()

    assert "keyword_analysis" in body
    assert 0 <= body["keyword_analysis"]["coverage_percentage"] <= 100
    assert "FastAPI" in body["keyword_analysis"]["matched_keywords"]
    assert "Docker" in body["keyword_analysis"]["missing_keywords"]
    assert "resume_quality" in body
    assert "matching_result" in body
