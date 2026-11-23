
from app.skill_extractor import extract_skills


def _skill_names(text: str) -> set[str]:
    return {item["skill"] for item in extract_skills(text)}


def analyze_match(resume_text: str, parsed_jd: dict) -> dict:
    """
    Compare resume evidence against skills found in the job description.

    Scoring policy:
    - Required skills: 80% of score
    - Preferred skills: 20% of score
    - If no preferred skills are detected, required skills receive 100%.
    - If neither group contains known skills, return no score.
    """
    sections = parsed_jd["sections"]

    required_text = "\n".join(
        [
            sections.get("required_qualifications", ""),
            sections.get("responsibilities", ""),
            sections.get("skills", ""),
        ]
    )

    preferred_text = sections.get("preferred_qualifications", "")

    required_skills = _skill_names(required_text)
    preferred_skills = _skill_names(preferred_text)

    # Avoid counting a skill in both categories.
    preferred_skills -= required_skills

    resume_items = extract_skills(resume_text)
    resume_skill_names = {item["skill"] for item in resume_items}
    resume_evidence = {
        item["skill"]: item["evidence"]
        for item in resume_items
    }

    required_matched = sorted(required_skills & resume_skill_names)
    required_missing = sorted(required_skills - resume_skill_names)

    preferred_matched = sorted(preferred_skills & resume_skill_names)
    preferred_missing = sorted(preferred_skills - resume_skill_names)

    if not required_skills and not preferred_skills:
        score = None
        score_status = "insufficient_detected_requirements"
    else:
        required_ratio = (
            len(required_matched) / len(required_skills)
            if required_skills else None
        )
        preferred_ratio = (
            len(preferred_matched) / len(preferred_skills)
            if preferred_skills else None
        )

        if required_ratio is not None and preferred_ratio is not None:
            score = round(
                100 * (0.8 * required_ratio + 0.2 * preferred_ratio)
            )
        elif required_ratio is not None:
            score = round(100 * required_ratio)
        else:
            score = round(100 * preferred_ratio)

        score_status = "calculated"

    return {
        "compatibility_score": score,
        "score_status": score_status,
        "score_explanation": (
            "Rule-based skill coverage score. Required skills contribute "
            "80% and preferred skills 20% when both groups are present. "
            "This is not an ATS score or hiring probability."
        ),
        "required_skills": sorted(required_skills),
        "required_matched": required_matched,
        "required_missing_evidence": required_missing,
        "preferred_skills": sorted(preferred_skills),
        "preferred_matched": preferred_matched,
        "preferred_missing_evidence": preferred_missing,
        "resume_skill_evidence": {
            skill: resume_evidence[skill]
            for skill in sorted(
                (required_skills | preferred_skills) & resume_skill_names
            )
        },
        "detected_resume_skills": sorted(resume_skill_names),
    }
