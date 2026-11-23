
from io import BytesIO

from docx import Document
from fastapi.testclient import TestClient

from app.main import app


client = TestClient(app)


def make_docx() -> bytes:
    document = Document()
    document.add_heading("Software Engineer Resume", level=1)
    document.add_paragraph("alex@example.com")
    document.add_heading("Professional Summary", level=2)
    document.add_paragraph(
        "Software developer experienced in Python backend applications."
    )
    document.add_heading("Technical Skills", level=2)
    document.add_paragraph("Python, FastAPI, SQL and REST API development")
    document.add_heading("Projects", level=2)
    document.add_paragraph(
        "Built a student project using Python and SQL."
    )
    document.add_paragraph(
        "Developed API endpoints and reduced manual work by 20%."
    )
    document.add_heading("Education", level=2)
    document.add_paragraph(
        "Bachelor of Technology in Computer Science, 2022-2026"
    )

    buffer = BytesIO()
    document.save(buffer)
    return buffer.getvalue()


VALID_JD = (
    "We need a Python developer with FastAPI experience "
    "to build backend APIs and maintain SQL databases."
)


def upload_docx(job_description: str = VALID_JD):
    return client.post(
        "/analyze",
        files={
            "file": (
                "resume.docx",
                make_docx(),
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
            )
        },
        data={"job_description": job_description},
    )


def test_root():
    response = client.get("/")

    assert response.status_code == 200
    assert response.json()["app"] == "HireLens AI"


def test_health():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_valid_docx_upload():
    response = upload_docx()

    assert response.status_code == 200

    body = response.json()

    assert "matching_result" in body
    assert "compatibility_score" in body["matching_result"]
    assert body["status"] == "analysis_completed"
    assert body["resume_characters"] > 0
    assert "FastAPI" in body["resume_preview"]


def test_api_includes_resume_quality_analysis():
    response = upload_docx()

    assert response.status_code == 200

    quality = response.json()["resume_quality"]

    assert 0 <= quality["score"] <= 100
    assert quality["max_score"] == 100
    assert quality["rating"]
    assert quality["executive_summary"]
    assert isinstance(quality["top_strengths"], list)
    assert isinstance(quality["main_improvements"], list)
    assert isinstance(quality["performance_metrics"], list)
    assert isinstance(quality["action_items"], list)
    assert isinstance(quality["limitations"], list)


def test_resume_quality_is_separate_from_skill_matching():
    response = upload_docx()

    assert response.status_code == 200

    body = response.json()

    assert "resume_quality" in body
    assert "matching_result" in body
    assert body["resume_quality"]["max_score"] == 100
    assert "compatibility_score" in body["matching_result"]


def test_reject_unsupported_file():
    response = client.post(
        "/analyze",
        files={"file": ("resume.txt", b"Some text", "text/plain")},
        data={"job_description": VALID_JD},
    )

    assert response.status_code == 415


def test_reject_short_job_description():
    response = upload_docx("Python job")

    assert response.status_code == 422


def test_reject_oversized_upload():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "resume.pdf",
                b"x" * (5 * 1024 * 1024 + 1),
                "application/pdf",
            )
        },
        data={"job_description": VALID_JD},
    )

    assert response.status_code == 413


def test_reject_corrupted_pdf():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "corrupted.pdf",
                b"This is not a valid PDF document.",
                "application/pdf",
            )
        },
        data={"job_description": VALID_JD},
    )

    assert response.status_code == 422
    assert "could not be read" in response.json()["detail"].lower()


def test_reject_corrupted_docx():
    response = client.post(
        "/analyze",
        files={
            "file": (
                "corrupted.docx",
                b"This is not a valid DOCX document.",
                "application/vnd.openxmlformats-officedocument."
                "wordprocessingml.document",
            )
        },
        data={"job_description": VALID_JD},
    )

    assert response.status_code == 422
    assert "could not be read" in response.json()["detail"].lower()
