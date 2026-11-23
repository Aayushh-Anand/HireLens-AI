
import re
from typing import Any


SECTION_PATTERNS = {
    "summary": (
        "summary", "professional summary", "profile",
        "career objective", "objective", "about me",
        "professional profile",
    ),
    "experience": (
        "experience", "work experience", "professional experience",
        "employment history", "internship", "internships",
        "work history",
    ),
    "education": (
        "education", "academic background", "educational background",
        "qualifications",
    ),
    "projects": (
        "projects", "personal projects", "academic projects",
        "key projects", "project experience",
    ),
    "skills": (
        "skills", "technical skills", "core competencies",
        "technologies", "tech stack", "technical expertise",
    ),
    "certifications": (
        "certifications", "certificates", "licenses",
        "certifications and certificates",
        "achievements & certificates",
        "achievements and certificates",
        "certifications & achievements",
        "certifications and achievements",
        "achievements and certifications",
    ),
    "achievements": (
        "achievements", "awards", "accomplishments", "honors",
        "honours",
    ),
}

SECTION_LOOKUP = {
    alias.lower(): section
    for section, aliases in SECTION_PATTERNS.items()
    for alias in aliases
}

ACTION_VERBS = {
    "built", "created", "developed", "designed", "implemented",
    "improved", "increased", "reduced", "automated", "optimized",
    "led", "launched", "delivered", "deployed", "managed",
    "analyzed", "engineered", "integrated", "tested", "maintained",
    "migrated", "trained", "generated", "streamlined", "resolved",
    "configured", "evaluated", "processed", "established",
    "contributed", "proposed", "refactored", "secured",
}

WEAK_PHRASES = (
    "hard working",
    "hardworking",
    "team player",
    "go getter",
    "responsible for",
    "worked on",
    "quick learner",
    "highly motivated",
    "results driven",
)

EMAIL_PATTERN = re.compile(
    r"\b[A-Z0-9._%+-]+@[A-Z0-9.-]+\.[A-Z]{2,}\b",
    re.IGNORECASE,
)

URL_PATTERN = re.compile(
    r"\b(?:https?://|www\.)\S+",
    re.IGNORECASE,
)

PHONE_PATTERN = re.compile(
    r"(?<!\w)(?:\+\d{1,3}[-.\s]?)?"
    r"(?:\(?\d{2,5}\)?[-.\s]?)?"
    r"\d{3,5}[-.\s]?\d{3,5}(?!\w)"
)

BULLET_PATTERN = re.compile(r"^\s*(?:[-*•▪◦‣]|\d+[.)])\s+")

# Numbers that look like years, percentages, counts, money, or durations.
# A number is only considered achievement evidence when its line also
# contains outcome/impact context. It is still a heuristic.
NUMBER_PATTERN = re.compile(
    r"(?<!\w)(?:"
    r"\d+(?:\.\d+)?\s?%|"
    r"\$\s?\d[\d,]*(?:\.\d+)?|"
    r"\d[\d,]*\+?\s*(?:users|customers|clients|projects|employees|"
    r"hours|days|weeks|months|years|records|requests|transactions|"
    r"teams|percent|k|m|million|billion)"
    r")(?!\w)",
    re.IGNORECASE,
)

IMPACT_TERMS = {
    "increased", "decreased", "reduced", "improved", "saved",
    "grew", "growth", "boosted", "cut", "raised", "lowered",
    "accelerated", "optimized", "achieved", "delivered",
    "generated", "served", "processed", "automated",
    "accuracy", "latency", "performance", "revenue", "cost",
    "efficiency", "conversion", "uptime", "users", "customers",
    "requests", "records", "transactions", "time",
}

DATE_ONLY_PATTERN = re.compile(
    r"^\s*(?:"
    r"(?:19|20)\d{2}(?:\s*[-–]\s*(?:(?:19|20)\d{2}|present))?|"
    r"(?:jan(?:uary)?|feb(?:ruary)?|mar(?:ch)?|apr(?:il)?|may|"
    r"jun(?:e)?|jul(?:y)?|aug(?:ust)?|sep(?:tember)?|oct(?:ober)?|"
    r"nov(?:ember)?|dec(?:ember)?)\s+(?:19|20)\d{2}"
    r")\s*$",
    re.IGNORECASE,
)


def _normalize(text: str) -> str:
    text = text.replace("\x00", " ")
    text = text.replace("\u200b", "")
    text = text.replace("\ufeff", "")
    text = re.sub(r"[ \t]+", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def _clean_heading(line: str) -> str:
    value = line.strip().strip(" :|•*-")
    value = re.sub(r"\s+", " ", value)
    return value.lower()


def _heading_name(line: str) -> str | None:
    candidate = _clean_heading(line)

    if candidate in SECTION_LOOKUP:
        return SECTION_LOOKUP[candidate]

    # Also recognize headings extracted with unusual spaces/punctuation.
    compact = re.sub(r"[^a-z0-9& ]", "", candidate)
    compact = re.sub(r"\s+", " ", compact).strip()

    if compact in SECTION_LOOKUP:
        return SECTION_LOOKUP[compact]

    return None


def _extract_sections(lines: list[str]) -> dict[str, list[str]]:
    sections: dict[str, list[str]] = {"other": []}
    current = "other"

    for line in lines:
        heading = _heading_name(line)

        if heading:
            current = heading
            sections.setdefault(current, [])
            continue

        sections.setdefault(current, []).append(line)

    return sections


def _section_text(
    sections: dict[str, list[str]],
    name: str,
) -> str:
    return "\n".join(sections.get(name, [])).strip()


def _word_count(text: str) -> int:
    return len(re.findall(r"\b[\w+#.-]+\b", text))


def _sentences(text: str) -> list[str]:
    return [
        part.strip()
        for part in re.split(r"(?<=[.!?])\s+|\n+", text)
        if part.strip()
    ]


def _unique(items: list[str]) -> list[str]:
    result = []
    seen = set()

    for item in items:
        normalized = item.strip().lower()
        if normalized and normalized not in seen:
            seen.add(normalized)
            result.append(item.strip())

    return result


def _section_present(
    sections: dict[str, list[str]],
    name: str,
) -> bool:
    return bool(_section_text(sections, name))


def _has_contact_information(text: str) -> bool:
    return bool(
        EMAIL_PATTERN.search(text)
        or PHONE_PATTERN.search(text)
        or URL_PATTERN.search(text)
    )


def _is_bullet(line: str) -> bool:
    return bool(BULLET_PATTERN.match(line))


def _has_impact_evidence(line: str) -> bool:
    """
    Only count a numeric line when it contains both a measurable pattern
    and language suggesting an outcome. This reduces false positives from
    graduation years, CGPA, percentages in education, and dates.
    """
    if not NUMBER_PATTERN.search(line):
        return False

    lowered = line.lower()
    words = set(re.findall(r"[a-z]+", lowered))

    return bool(words.intersection(IMPACT_TERMS))


def _starts_with_action_verb(line: str) -> bool:
    cleaned = BULLET_PATTERN.sub("", line).strip()
    words = re.findall(r"[a-zA-Z]+", cleaned.lower())
    return bool(words and words[0] in ACTION_VERBS)


def _content_lines(sections: dict[str, list[str]]) -> list[str]:
    selected = []

    for section_name in ("experience", "projects", "achievements"):
        selected.extend(sections.get(section_name, []))

    return [line for line in selected if line.strip()]


def _build_executive_summary(
    sections: dict[str, list[str]],
    word_count: int,
) -> str:
    """
    Summarize the detected sections without copying the entire skills
    section. This is an extractive, rule-based summary, not generative AI.
    """
    parts = []

    summary_text = _section_text(sections, "summary")
    skills_text = _section_text(sections, "skills")
    experience_text = _section_text(sections, "experience")
    projects_text = _section_text(sections, "projects")
    education_text = _section_text(sections, "education")
    certifications_text = _section_text(sections, "certifications")
    achievements_text = _section_text(sections, "achievements")

    if summary_text:
        first_sentences = _sentences(summary_text)[:2]
        excerpt = " ".join(first_sentences)
        if len(excerpt) > 320:
            excerpt = excerpt[:317].rsplit(" ", 1)[0] + "..."
        parts.append(excerpt)

    if skills_text:
        skill_terms = re.split(r"[,;|\n•]", skills_text)
        skill_terms = [
            re.sub(r"\s+", " ", term).strip(" :.-")
            for term in skill_terms
        ]
        skill_terms = [
            term for term in skill_terms
            if 1 <= len(term) <= 45 and len(term.split()) <= 6
        ]
        skill_terms = _unique(skill_terms)[:6]

        if skill_terms:
            parts.append(
                "The skills section lists technologies including "
                + ", ".join(skill_terms)
                + "."
            )
        else:
            parts.append("A skills section was detected.")

    if experience_text:
        count = len([line for line in experience_text.splitlines() if line.strip()])
        parts.append(
            f"The resume includes an experience section with {count} "
            "non-empty extracted line(s)."
        )

    if projects_text:
        count = len([line for line in projects_text.splitlines() if line.strip()])
        parts.append(
            f"It also includes projects with {count} "
            "non-empty extracted line(s)."
        )

    if education_text:
        excerpt = " ".join(_sentences(education_text)[:1])
        if excerpt:
            excerpt = excerpt[:180]
            parts.append("Education information detected: " + excerpt)
        else:
            parts.append("An education section was detected.")

    if certifications_text:
        parts.append("A certifications or certificates section was detected.")

    if achievements_text:
        parts.append("A separate achievements section was detected.")

    if not parts:
        parts.append(
            f"The resume contains approximately {word_count} extracted "
            "words, but standard section headings were not recognized. "
            "The summary may be limited by the document's heading format."
        )

    result = " ".join(parts)
    if len(result) > 1000:
        result = result[:997].rsplit(" ", 1)[0] + "..."
    return result


def analyze_resume_quality(resume_text: str) -> dict[str, Any]:
    """
    Explainable heuristic resume content assessment.

    Not an ATS score, hiring probability, visual-format inspection,
    employment verification, or a guarantee of resume performance.
    """
    text = _normalize(resume_text)

    if not text:
        raise ValueError("Resume text must not be empty.")

    lines = [line.strip() for line in text.splitlines() if line.strip()]
    word_count = _word_count(text)
    sections = _extract_sections(lines)

    summary_text = _section_text(sections, "summary")
    experience_text = _section_text(sections, "experience")
    project_text = _section_text(sections, "projects")
    skills_text = _section_text(sections, "skills")
    education_text = _section_text(sections, "education")
    certifications_text = _section_text(sections, "certifications")
    achievements_text = _section_text(sections, "achievements")

    present_sections = [
        name for name in SECTION_PATTERNS
        if _section_present(sections, name)
    ]

    experience_lines = [
        line for line in experience_text.splitlines() if line.strip()
    ]
    project_lines = [
        line for line in project_text.splitlines() if line.strip()
    ]
    achievement_section_lines = [
        line for line in achievements_text.splitlines() if line.strip()
    ]
    certification_lines = [
        line for line in certifications_text.splitlines() if line.strip()
    ]

    evidence_lines = (
        experience_lines + project_lines + achievement_section_lines
    )
    quantified_lines = [
        line for line in evidence_lines if _has_impact_evidence(line)
    ]
    action_lines = [
        line for line in experience_lines + project_lines
        if _starts_with_action_verb(line)
    ]

    lower_text = re.sub(r"\s+", " ", text.lower()).strip()
    generic_phrases = [phrase
    for phrase in WEAK_PHRASES
    if re.search(
        r"\b" + re.escape(phrase) + r"\b",
        lower_text,
    )
]

    contact_present = _has_contact_information(text)
    experience_or_projects_present = bool(
        experience_text or project_text
    )
    section_count = len(present_sections)

    # Each metric has a fixed weight. Checks are transparent and binary.
    metric_definitions = [
        {
            "key": "content_completeness",
            "label": "Content completeness",
            "weight": 25,
            "checks": [
                (contact_present, "Contact information detected"),
                (_section_present(sections, "education"),
                 "Education section detected"),
                (_section_present(sections, "skills"),
                 "Skills section detected"),
                (experience_or_projects_present,
                 "Experience or projects section detected"),
            ],
        },
        {
            "key": "achievement_evidence",
            "label": "Quantified achievement evidence",
            "weight": 25,
            "checks": [
                (len(quantified_lines) >= 1,
                 "At least one potential measurable outcome line detected"),
                (len(quantified_lines) >= 3,
                 "Three or more potential measurable outcome lines detected"),
            ],
        },
        {
            "key": "impact_language",
            "label": "Action-oriented experience",
            "weight": 20,
            "checks": [
                (len(action_lines) >= 1,
                 "An experience/project line begins with a recognized action verb"),
                (len(action_lines) >= 3,
                 "Three or more experience/project lines begin with recognized action verbs"),
            ],
        },
        {
            "key": "structure",
            "label": "Recognized section structure",
            "weight": 20,
            "checks": [
                (section_count >= 3,
                 "Three or more recognized resume sections detected"),
                (bool(summary_text),
                 "Summary or objective section detected"),
                (
                    bool(project_text or certifications_text or achievements_text),
                    "Projects, certifications, or achievements section detected",
                ),
            ],
        },
        {
            "key": "readability",
            "label": "Extracted-text indicators",
            "weight": 10,
            "checks": [
                (150 <= word_count <= 1200,
                 "Extracted word count is within a broad resume range"),
                (bool(lines) and max(map(len, lines)) <= 300,
                 "No extremely long extracted line detected"),
            ],
        },
    ]

    metrics = []
    total_score = 0.0

    for definition in metric_definitions:
        checks = definition["checks"]
        passed = sum(1 for condition, _ in checks if condition)
        ratio = passed / len(checks) if checks else 0.0
        score = round(ratio * definition["weight"], 1)
        total_score += score

        metrics.append({
            "key": definition["key"],
            "label": definition["label"],
            "score": score,
            "max_score": definition["weight"],
            "percentage": round(ratio * 100),
            "evidence": [
                description for condition, description in checks
                if condition
            ],
            "not_detected": [
                description for condition, description in checks
                if not condition
            ],
        })

    score = max(0, min(100, round(total_score)))

    if score >= 85:
        rating = "Strong"
    elif score >= 70:
        rating = "Good"
    elif score >= 50:
        rating = "Needs improvement"
    else:
        rating = "Needs significant improvement"

    strengths = []
    improvements = []
    action_items = []

    if contact_present:
        strengths.append({
            "title": "Contact information detected",
            "evidence": "The extracted text contains a recognizable email, phone-like number, or URL.",
        })
    else:
        improvements.append({
            "title": "Check contact information",
            "reason": "No recognizable email address, phone-like number, or URL was detected.",
            "priority": "high",
        })
        action_items.append({
            "priority": "high",
            "action": "Ensure your resume includes a professional email address and an appropriate contact method.",
        })

    if skills_text:
        strengths.append({
            "title": "Skills section detected",
            "evidence": "A recognized skills heading and its content were found.",
        })
    else:
        improvements.append({
            "title": "Add a clearly labeled skills section",
            "reason": "A standard skills heading was not detected. An unusual heading or extraction issue may explain this.",
            "priority": "high",
        })
        action_items.append({
            "priority": "high",
            "action": "Add a skills section listing relevant technologies you can substantiate.",
        })

    if experience_text:
        strengths.append({
            "title": "Experience section detected",
            "evidence": "A recognizable experience heading was found.",
        })
    elif project_text:
        strengths.append({
            "title": "Projects section detected",
            "evidence": "Projects can demonstrate practical skills and implementation experience.",
        })
    else:
        improvements.append({
            "title": "Show relevant experience or projects",
            "reason": "No standard experience or projects heading was detected.",
            "priority": "high",
        })
        action_items.append({
            "priority": "high",
            "action": "Include relevant work, internships, or projects and explain your individual contribution.",
        })

    if quantified_lines:
        strengths.append({
            "title": "Potential measurable outcomes detected",
            "evidence": (
                f"{len(quantified_lines)} experience/project/achievement "
                "line(s) contain a measurable pattern with impact-related "
                "language. Verify that each result is accurate."
            ),
        })
    else:
        improvements.append({
            "title": "Show measurable impact where truthful",
            "reason": "No clear combination of measurable patterns and outcome-related language was detected in experience, projects, or achievements.",
            "priority": "medium",
        })
        action_items.append({
            "priority": "medium",
            "action": "Where accurate, show scale or outcomes such as time saved, performance improved, users served, or errors reduced.",
        })

    if action_lines:
        strengths.append({
            "title": "Action-oriented project or experience lines",
            "evidence": (
                f"{len(action_lines)} line(s) begin with a recognized "
                "action verb."
            ),
        })
    else:
        improvements.append({
            "title": "Make experience and project descriptions more specific",
            "reason": "The analyzer did not recognize its predefined action verbs at the beginning of experience/project lines.",
            "priority": "medium",
        })
        action_items.append({
            "priority": "medium",
            "action": "Begin relevant bullet points with accurate verbs such as developed, implemented, tested, or optimized.",
        })

    if summary_text:
        strengths.append({
            "title": "Professional summary detected",
            "evidence": "A recognized summary or objective heading was found.",
        })
    else:
        improvements.append({
            "title": "Consider adding a targeted summary",
            "reason": "A standard summary/objective heading was not detected. It is optional for some resume formats.",
            "priority": "low",
        })
        action_items.append({
            "priority": "low",
            "action": "Consider a concise role-specific summary highlighting your strongest relevant evidence.",
        })

        if generic_phrases:
            improvements.append({
            "title": "Replace generic phrases with evidence",
            "reason": (
                "Potentially generic phrases detected: "
                + ", ".join(generic_phrases)
            ),
            "priority": "medium",
        })
        action_items.append({
            "priority": "medium",
            "action": (
                "Replace generic claims with specific examples, "
                "technical contributions, or verifiable outcomes."
            ),
        })

    if word_count < 150:
        improvements.append({
            "title": "Check resume detail",
            "reason": f"Only {word_count} words were extracted. This can be valid for some resumes, but may indicate incomplete extraction or limited detail.",
            "priority": "medium",
        })
    elif word_count > 1200:
        improvements.append({
            "title": "Review resume length",
            "reason": f"{word_count} words were extracted. Consider removing repetition if the document is longer than needed for your experience.",
            "priority": "low",
        })

    if not education_text:
        improvements.append({
            "title": "Check education section",
            "reason": "A standard education heading was not detected.",
            "priority": "low",
        })

    if not certification_lines and not achievement_section_lines:
        action_items.append({
            "priority": "low",
            "action": "If relevant, include certifications or achievements that support your target role; these sections are optional.",
        })

    if not strengths:
        strengths.append({
            "title": "Resume text extracted",
            "evidence": f"The parser extracted {word_count} words for assessment.",
        })

    if not improvements:
        improvements.append({
            "title": "Review relevance for the target role",
            "reason": "No major issue was detected by these basic text heuristics. This does not guarantee resume effectiveness.",
            "priority": "low",
        })

    executive_summary = _build_executive_summary(sections, word_count)

    return {
        "score": score,
        "max_score": 100,
        "rating": rating,
        "score_explanation": (
            "A heuristic resume-content quality indicator based on "
            "content completeness, potential measurable outcomes, "
            "action-oriented language, recognized section structure, "
            "and extracted-text indicators. It is not an ATS score "
            "or a hiring prediction."
        ),
        "executive_summary": executive_summary,
        "top_strengths": strengths[:6],
        "main_improvements": improvements[:8],
        "performance_metrics": metrics,
        "action_items": action_items[:10],
        "resume_statistics": {
            "word_count": word_count,
            "character_count": len(text),
            "line_count": len(lines),
            "recognized_sections": present_sections,
            "quantified_lines_detected": len(quantified_lines),
            "action_oriented_lines_detected": len(action_lines),
            "generic_phrases_detected": generic_phrases,
        },
        "limitations": [
            "Assessment uses extracted text and predefined heuristics; it does not fully understand context.",
            "Visual layout, font size, spacing, columns, and page design are not evaluated.",
            "A measurable pattern is not proof of a genuine achievement; review the evidence manually.",
            "A missing heading may reflect an unusual heading or a parsing limitation.",
            "The score does not measure hiring probability, guarantee ATS compatibility, or verify resume claims.",
        ],
    }
