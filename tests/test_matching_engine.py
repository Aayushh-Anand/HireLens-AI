
from app.jd_parser import parse_job_description
from app.skill_extractor import extract_skills
from app.matching_engine import analyze_match


def test_extract_skill_aliases():
    skills = extract_skills(
        "Built APIs with Python, FastAPI, JS and sklearn."
    )
    names = {item["skill"] for item in skills}

    assert "Python" in names
    assert "FastAPI" in names
    assert "JavaScript" in names
    assert "scikit-learn" in names


def test_java_does_not_match_javascript():
    skills = extract_skills("Developed a frontend using JavaScript.")
    names = {item["skill"] for item in skills}

    assert "JavaScript" in names
    assert "Java" not in names


def test_required_and_preferred_skill_matching():
    jd = parse_job_description(
        "Required Qualifications:\nPython and SQL experience.\n"
        "Preferred Qualifications:\nExperience with Docker."
    )

    result = analyze_match(
        "Developed projects using Python and SQL.",
        jd,
    )

    assert result["required_matched"] == ["Python", "SQL"]
    assert result["preferred_missing_evidence"] == ["Docker"]
    assert result["compatibility_score"] == 80


def test_no_detected_skills_returns_no_score():
    jd = parse_job_description(
        "Role Overview:\nSeeking a motivated team player."
    )

    result = analyze_match(
        "Worked on general assignments.",
        jd,
    )

    assert result["compatibility_score"] is None
    assert result["score_status"] == "insufficient_detected_requirements"


def test_match_includes_evidence():
    jd = parse_job_description(
        "Required Qualifications:\nPython experience required."
    )

    result = analyze_match(
        "Developed a project using Python.",
        jd,
    )

    assert "Python" in result["resume_skill_evidence"]
    assert "Python" in result["resume_skill_evidence"]["Python"]

def test_empty_resume_has_no_matched_skills():
    jd = parse_job_description(
        "Required Qualifications:\nPython and SQL experience."
    )

    result = analyze_match("", jd)

    assert result["required_matched"] == []
    assert result["required_missing_evidence"] == ["Python", "SQL"]
    assert result["compatibility_score"] == 0


def test_required_skill_is_not_double_counted_as_preferred():
    jd = parse_job_description(
        "Required Qualifications:\nPython experience.\n"
        "Preferred Qualifications:\nPython and Docker experience."
    )

    result = analyze_match(
        "Built projects with Python and Docker.",
        jd,
    )

    assert "Python" in result["required_skills"]
    assert "Python" not in result["preferred_skills"]
    assert result["required_matched"] == ["Python"]
    assert result["preferred_matched"] == ["Docker"]


def test_unrecognized_jd_skills_do_not_create_a_score():
    jd = parse_job_description(
        "Required Qualifications:\nExperience with an imaginary tool."
    )

    result = analyze_match(
        "Worked on software development projects.",
        jd,
    )

    assert result["required_skills"] == []
    assert result["compatibility_score"] is None
    assert result["score_status"] == "insufficient_detected_requirements"

def test_skill_list_evidence_is_precise():
    from app.skill_extractor import extract_skills

    skills = extract_skills(
        "Languages: JavaScript, Java (DSA), Python, SQL"
    )
    evidence = {item["skill"]: item["evidence"] for item in skills}

    assert evidence["Python"] == "Python"
    assert evidence["SQL"] == "SQL"
    assert evidence["Java"] == "Java (DSA)"
    assert evidence["JavaScript"] == "JavaScript"


def test_action_sentence_evidence_keeps_context():
    from app.skill_extractor import extract_skills

    skills = extract_skills(
        "Developed REST APIs using Python and SQL for a web application."
    )
    evidence = {item["skill"]: item["evidence"] for item in skills}

    assert "Developed REST APIs using Python and SQL" in evidence["Python"]
    assert "Developed REST APIs using Python and SQL" in evidence["SQL"]


def test_java_does_not_match_inside_javascript():
    from app.skill_extractor import extract_skills

    skills = extract_skills("Developed a frontend using JavaScript.")
    names = {item["skill"] for item in skills}

    assert "JavaScript" in names
    assert "Java" not in names

def test_semantic_suggestions_do_not_treat_heading_as_strong_evidence():
    from app.semantic_matcher import find_semantic_suggestions

    suggestions = find_semantic_suggestions(
        "Backend & APIs\n"
        "Built REST APIs using Python for a deployed project.",
        "Develop REST APIs and deploy production services.",
    )

    assert all(
        item["resume_evidence"] != "Backend & APIs"
        for item in suggestions
    )
    assert all(
        item["counts_as_confirmed_match"] is False
        for item in suggestions
    )
