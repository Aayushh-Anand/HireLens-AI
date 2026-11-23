
from app.jd_parser import clean_job_description, parse_job_description


def test_clean_job_description():
    result = clean_job_description(
        "  Python   Developer  \n\n  Build APIs   "
    )
    assert result == "Python Developer\nBuild APIs"


def test_parse_recognized_sections():
    jd = """
    Role Overview
    Build AI applications.

    Responsibilities:
    Develop REST APIs.
    Evaluate machine learning models.

    Required Qualifications:
    Python and SQL experience.

    Preferred Qualifications:
    Experience with Docker.

    Education:
    Bachelor's degree in Computer Science.
    """

    result = parse_job_description(jd)
    sections = result["sections"]

    assert "Build AI applications." in sections["overview"]
    assert "Develop REST APIs." in sections["responsibilities"]
    assert "Python and SQL experience." in sections["required_qualifications"]
    assert "Experience with Docker." in sections["preferred_qualifications"]
    assert "Bachelor's degree" in sections["education"]


def test_unknown_heading_content_is_preserved():
    jd = """
    Role Overview
    Build useful AI tools.

    Company Benefits:
    Flexible working hours.
    """

    result = parse_job_description(jd)

    assert "Company Benefits:" in result["sections"]["overview"]
    assert "Flexible working hours." in result["sections"]["overview"]


def test_empty_job_description():
    result = parse_job_description("   \n  ")

    assert result["cleaned_text"] == ""
    assert result["recognized_sections"] == []


def test_markdown_headings():
    result = parse_job_description(
        "## Responsibilities:\n- Build APIs"
    )

    assert "- Build APIs" in result["sections"]["responsibilities"]

def test_inline_jd_headings_are_split():
    jd = (
        "Role Overview: Build AI-powered applications. "
        "Responsibilities: Develop REST APIs. "
        "Required Qualifications: Python and SQL experience. "
        "Preferred Qualifications: Experience with Docker. "
        "Education: Bachelor's degree in Computer Science."
    )

    result = parse_job_description(jd)
    sections = result["sections"]

    assert "Build AI-powered applications." in sections["overview"]
    assert "Develop REST APIs." in sections["responsibilities"]
    assert "Python and SQL experience." in sections["required_qualifications"]
    assert "Experience with Docker." in sections["preferred_qualifications"]
    assert "Bachelor's degree" in sections["education"]

def test_inline_ai_engineer_jd_sections():
    from app.jd_parser import parse_job_description

    jd = (
        "We are hiring a Junior AI Engineer. "
        "Role & responsibilities Design and deploy AI models. "
        "Collaborate with cross-functional teams. "
        "Required Qualifications Strong Python skills. "
        "Experience with TensorFlow or PyTorch. "
        "Preferred Qualifications Experience with Docker. "
        "Education Bachelor's degree in Computer Science."
    )

    result = parse_job_description(jd)
    sections = result["sections"]

    assert "Design and deploy AI models" in sections["responsibilities"]
    assert "Strong Python skills" in sections["required_qualifications"]
    assert "Experience with TensorFlow or PyTorch" in sections["required_qualifications"]
    assert "Experience with Docker" in sections["preferred_qualifications"]
    assert "Bachelor's degree" in sections["education"]

def test_real_world_jd_headings_are_classified():
    from app.jd_parser import parse_job_description

    jd = (
        "Junior AI/ML Engineer. "
        "What you'll do: Develop REST APIs using Python. "
        "What we're looking for: Strong Python and SQL skills. "
        "Nice to have: Experience with Docker and LangChain. "
        "Education and experience: Bachelor's degree in Computer Science."
    )

    sections = parse_job_description(jd)["sections"]

    assert "Develop REST APIs using Python" in sections["responsibilities"]
    assert "Strong Python and SQL skills" in sections["required_qualifications"]
    assert "Docker" in sections["preferred_qualifications"]
    assert "LangChain" in sections["preferred_qualifications"]
    assert "Bachelor's degree" in sections["education"]

def test_what_were_looking_for_keeps_entire_section():
    from app.jd_parser import parse_job_description

    jd = (
        "What we're looking for: "
        "- Strong programming skills in Python. "
        "- Understanding of machine learning and deep learning fundamentals. "
        "- Experience with SQL and relational databases. "
        "- Familiarity with Git and REST API development. "
        "- Good analytical and problem-solving skills. "
        "Nice to have: Experience with Docker. "
        "Education and experience: Bachelor's degree in Computer Science."
    )

    sections = parse_job_description(jd)["sections"]

    assert "Strong programming skills in Python" in sections["required_qualifications"]
    assert "machine learning and deep learning" in sections["required_qualifications"]
    assert "SQL and relational databases" in sections["required_qualifications"]
    assert "Git and REST API development" in sections["required_qualifications"]
    assert "Docker" in sections["preferred_qualifications"]
    assert "Bachelor's degree" in sections["education"]
