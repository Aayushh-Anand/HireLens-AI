
import asyncio
from pathlib import Path
from typing import Any

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from app.ats_keyword_analyzer import analyze_keyword_coverage
from app.document_parser import (
    DocumentParsingError,
    extract_resume_text,
)
from app.jd_parser import parse_job_description
from app.matching_engine import analyze_match
from app.resume_quality_analyzer import analyze_resume_quality
from app.semantic_matcher import find_semantic_suggestions


app = FastAPI(
    title="HireLens AI",
    description=(
        "Resume quality analysis, job description keyword coverage, "
        "explainable skill matching, and optional semantic suggestions."
    ),
    version="0.5.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)

MAX_FILE_SIZE = 5 * 1024 * 1024
MAX_JD_LENGTH = 15_000
ALLOWED_EXTENSIONS = {".pdf", ".docx"}


class AnalysisResponse(BaseModel):
    filename: str
    resume_characters: int
    job_description_characters: int
    resume_preview: str
    job_description_preview: str
    jd_sections: dict[str, str]
    recognized_jd_sections: list[str]
    matching_result: dict[str, Any]
    semantic_suggestions: list[dict[str, Any]] = Field(
        default_factory=list
    )
    resume_quality: dict[str, Any]
    keyword_analysis: dict[str, Any]
    status: str


@app.get("/")
def root():
    return {
        "app": "HireLens AI",
        "status": "running",
        "phase": "ats-keyword-analysis",
    }


@app.get("/health")
def health():
    return {"status": "healthy"}


@app.post("/analyze", response_model=AnalysisResponse)
async def analyze_resume(
    file: UploadFile = File(...),
    job_description: str = Form(...),
):
    filename = Path(file.filename or "").name
    extension = Path(filename).suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        await file.close()
        raise HTTPException(
            status_code=415,
            detail="Only PDF and DOCX resumes are supported.",
        )

    try:
        content = await file.read(MAX_FILE_SIZE + 1)
    finally:
        await file.close()

    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(
            status_code=413,
            detail="Resume file must be 5 MB or smaller.",
        )

    if not content:
        raise HTTPException(
            status_code=400,
            detail="The uploaded file is empty.",
        )

    jd = job_description.strip()

    if len(jd) < 30:
        raise HTTPException(
            status_code=422,
            detail=(
                "Please provide a job description "
                "with at least 30 characters."
            ),
        )

    if len(jd) > MAX_JD_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=(
                "Job description must be 15,000 characters "
                "or fewer."
            ),
        )

    try:
        resume_text = extract_resume_text(filename, content)
    except DocumentParsingError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc

    try:
        resume_quality = await asyncio.to_thread(
            analyze_resume_quality,
            resume_text,
        )
        keyword_analysis = await asyncio.to_thread(
            analyze_keyword_coverage,
            resume_text,
            jd,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=422,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        raise HTTPException(
            status_code=500,
            detail="Resume or keyword analysis failed.",
        ) from exc

    # Existing JD parser and skill-matching engine are retained.
    parsed_jd = parse_job_description(jd)
    matching_result = analyze_match(resume_text, parsed_jd)

    sections = parsed_jd["sections"]

    semantic_requirement_text = "\n".join(
        sections.get(section, "")
        for section in (
            "required_qualifications",
            "responsibilities",
            "skills",
            "preferred_qualifications",
        )
    )

    try:
        semantic_suggestions = await asyncio.to_thread(
            find_semantic_suggestions,
            resume_text,
            semantic_requirement_text,
        )
    except Exception:
        semantic_suggestions = []

    return AnalysisResponse(
        filename=filename,
        resume_characters=len(resume_text),
        job_description_characters=len(jd),
        resume_preview=resume_text[:500],
        job_description_preview=parsed_jd["cleaned_text"][:300],
        jd_sections=parsed_jd["sections"],
        recognized_jd_sections=parsed_jd["recognized_sections"],
        matching_result=matching_result,
        semantic_suggestions=semantic_suggestions,
        resume_quality=resume_quality,
        keyword_analysis=keyword_analysis,
        status="analysis_completed",
    )
