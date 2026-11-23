
import pytest

from app.resume_quality_analyzer import analyze_resume_quality


SAMPLE_RESUME = """
Alex Morgan
alex.morgan@example.com
https://example.com

PROFESSIONAL SUMMARY
Software developer focused on Python backend applications.

TECHNICAL SKILLS
Python, FastAPI, SQL, Git, REST APIs

EXPERIENCE
Developed REST APIs serving 1200 users.
Automated reporting and reduced processing time by 30%.
Built backend services and improved response time by 20%.

PROJECTS
Created a student management application using Python and SQL.
Implemented authentication and tested API endpoints.

EDUCATION
Bachelor of Technology, Computer Science
2022 - 2026
"""

RESUME_WITH_ACHIEVEMENTS = """
Taylor Smith
taylor@example.com

SKILLS
Python, SQL

EDUCATION
Bachelor of Technology, 2023 - 2027
CGPA: 8.0
Class XII: 78%

PROJECTS
Built a recommendation system using Python.
Improved recommendation response time by 25%.

ACHIEVEMENTS & CERTIFICATES
Introduction to Generative AI, Google Cloud, 2025
Completed training on Large Language Model fundamentals.
"""


def test_analyzer_returns_expected_top_level_fields():
    result = analyze_resume_quality(SAMPLE_RESUME)

    expected = {
        "score",
        "max_score",
        "rating",
        "score_explanation",
        "executive_summary",
        "top_strengths",
        "main_improvements",
        "performance_metrics",
        "action_items",
        "resume_statistics",
        "limitations",
    }

    assert expected.issubset(result.keys())


def test_score_is_within_valid_range():
    result = analyze_resume_quality(SAMPLE_RESUME)

    assert 0 <= result["score"] <= 100
    assert result["max_score"] == 100


def test_resume_sections_are_recognized():
    result = analyze_resume_quality(SAMPLE_RESUME)

    sections = result["resume_statistics"]["recognized_sections"]

    assert "experience" in sections
    assert "projects" in sections
    assert "education" in sections
    assert "skills" in sections
    assert "summary" in sections


def test_quantified_impact_is_detected():
    result = analyze_resume_quality(SAMPLE_RESUME)

    assert (
        result["resume_statistics"]["quantified_lines_detected"] >= 1
    )


def test_education_numbers_are_not_automatically_achievements():
    result = analyze_resume_quality(RESUME_WITH_ACHIEVEMENTS)

    # Graduation dates, CGPA and Class XII percentage alone should not
    # be counted as quantified achievement lines.
    assert (
        result["resume_statistics"]["quantified_lines_detected"] == 1
    )


def test_action_oriented_lines_are_detected():
    result = analyze_resume_quality(SAMPLE_RESUME)

    assert (
        result["resume_statistics"]["action_oriented_lines_detected"]
        >= 1
    )


def test_performance_metrics_have_valid_scores():
    result = analyze_resume_quality(SAMPLE_RESUME)

    assert result["performance_metrics"]

    for metric in result["performance_metrics"]:
        assert 0 <= metric["score"] <= metric["max_score"]
        assert 0 <= metric["percentage"] <= 100
        assert "evidence" in metric
        assert "not_detected" in metric


def test_score_explanation_does_not_claim_ats_score():
    result = analyze_resume_quality(SAMPLE_RESUME)

    explanation = result["score_explanation"].lower()

    assert "not an ats score" in explanation
    assert "hiring prediction" in explanation


def test_empty_resume_text_is_rejected():
    with pytest.raises(ValueError):
        analyze_resume_quality("   \n  ")


def test_minimal_resume_returns_structured_result():
    result = analyze_resume_quality(
        "Taylor\nA short resume text without standard headings."
    )

    assert 0 <= result["score"] <= 100
    assert isinstance(result["top_strengths"], list)
    assert isinstance(result["main_improvements"], list)
    assert isinstance(result["action_items"], list)
    assert isinstance(result["limitations"], list)


def test_generic_phrases_are_flagged():
    resume = """
    Jordan
    jordan@example.com

    SKILLS
    Python

    PROJECTS
    Worked on a project. I am a hard working team player.
    """

    result = analyze_resume_quality(resume)

    assert result["resume_statistics"]["generic_phrases_detected"]
    assert any(
        "generic phrases" in item["title"].lower()
        for item in result["main_improvements"]
    )


def test_achievements_and_certificates_heading_is_recognized():
    result = analyze_resume_quality(RESUME_WITH_ACHIEVEMENTS)

    sections = result["resume_statistics"]["recognized_sections"]

    assert "certifications" in sections


def test_executive_summary_does_not_copy_entire_skills_section():
    result = analyze_resume_quality(SAMPLE_RESUME)

    summary = result["executive_summary"]

    assert summary
    assert len(summary) <= 1000
    assert "Python" in summary
    assert "The skills section lists technologies" in summary


def test_executive_summary_mentions_detected_certifications():
    result = analyze_resume_quality(RESUME_WITH_ACHIEVEMENTS)

    assert (
        "certifications or certificates section was detected"
        in result["executive_summary"]
    )


def test_quality_score_is_separate_from_job_matching():
    result = analyze_resume_quality(SAMPLE_RESUME)

    assert result["max_score"] == 100
    assert "compatibility_score" not in result
