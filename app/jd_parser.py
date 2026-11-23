
import re
from typing import Any


SECTION_ALIASES = {
    "overview": (
        "role overview", "overview", "job summary",
        "about the role", "about the job", "job description",
        "position summary", "company overview",
    ),
    "responsibilities": (
        "roles and responsibilities", "role & responsibilities",
        "role and responsibilities", "key responsibilities",
        "job responsibilities", "responsibilities",
        "what you will do", "what you'll do", "duties", "key duties",
    ),
    "required_qualifications": (
        "preferred candidate profile", "required qualifications",
        "minimum qualifications", "basic qualifications",
        "what we're looking for", "what we are looking for",
        "what we're looking for:", "what you need",
        "requirements", "qualifications", "must have",
        "essential skills",
    ),
    "preferred_qualifications": (
        "preferred qualifications", "preferred requirements",
        "nice to have", "good to have", "bonus qualifications",
        "desirable skills",
    ),
    "skills": (
        "technical requirements", "technical skills", "required skills",
        "key skills", "tools and technologies", "technology stack",
        "skills",
    ),
    "education": (
        "education and experience", "educational qualifications",
        "academic qualifications", "degree requirements", "education",
    ),
}

# Prefer longer, more specific headings over shorter overlapping aliases.
_HEADING_ALIASES = sorted(
    [
        (alias.rstrip(":").strip(), section)
        for section, aliases in SECTION_ALIASES.items()
        for alias in aliases
    ],
    key=lambda item: len(item[0]),
    reverse=True,
)

_PREFERRED_CUES = (
    "nice to have",
    "good to have",
    "preferred",
    "desirable",
    "bonus",
    "would be an advantage",
    "is an advantage",
)

_MARKDOWN_PREFIX = re.compile(r"^\s{0,3}#{1,6}\s+")
_BULLET_PREFIX = re.compile(r"^\s*(?:[-*•▪◦]|\d+[.)])\s*")


def _normalize(text: str) -> str:
    text = text.replace("\ufeff", "").replace("\u200b", "")
    text = text.replace("\r\n", "\n").replace("\r", "\n")
    lines = []

    for line in text.splitlines():
        line = re.sub(r"[ \t]+", " ", line).strip()
        if line:
            lines.append(line)

    return "\n".join(lines)


def clean_job_description(job_description: str) -> str:
    """Public compatibility function used by existing tests and callers."""
    return _normalize(job_description)


def _clean_heading(text: str) -> str:
    text = _MARKDOWN_PREFIX.sub("", text)
    text = _BULLET_PREFIX.sub("", text)
    text = text.strip().strip(" :|•▪◦*-\t")
    return re.sub(r"\s+", " ", text).lower()


def _heading_from_line(line: str) -> str | None:
    cleaned = _clean_heading(line)

    for alias, section in _HEADING_ALIASES:
        if cleaned == alias.lower():
            return section

    return None


def _section_for_heading(heading: str) -> str | None:
    normalized = _clean_heading(heading)

    for alias, section in _HEADING_ALIASES:
        if normalized == alias.lower():
            return section

    return None


def _build_heading_regex() -> re.Pattern:
    alternatives = "|".join(
        re.escape(alias).replace(r"\ ", r"\s+")
        for alias, _ in _HEADING_ALIASES
    )

    return re.compile(
        rf"(?<!\w)(?P<heading>{alternatives})"
        rf"(?=\s*(?::|[-–—]\s|\s|$))"
        rf"\s*:?\s*",
        re.IGNORECASE,
    )


_HEADING_RE = _build_heading_regex()


def _find_inline_headings(
    line: str,
) -> list[tuple[int, int, str]]:
    """
    Detect headings at the beginning of a line or after a sentence
    boundary. Avoid treating ordinary words inside a sentence as headings.
    """
    normalized = _MARKDOWN_PREFIX.sub("", line)
    candidates = []

    for match in _HEADING_RE.finditer(normalized):
        prefix = normalized[:match.start()]

        # A heading later in a line must have a recognizable boundary.
        # For example: "... products. Responsibilities: Build APIs."
        if prefix.strip() and not re.search(
            r"(?:[.!?;:]|[-–—])\s*$",
            prefix,
        ):
            continue

        section = _section_for_heading(match.group("heading"))
        if section:
            candidates.append((match.start(), match.end(), section))

    candidates.sort(key=lambda item: (item[0], -(item[1] - item[0])))

    result = []
    last_end = -1

    for start, end, section in candidates:
        if start < last_end:
            continue
        result.append((start, end, section))
        last_end = end

    return result


def _split_items(text: str) -> list[str]:
    items = re.split(r"\n+|;\s*", text)
    return [
        item.strip(" \t•▪◦*-\u2022")
        for item in items
        if item.strip(" \t•▪◦*-\u2022")
    ]


def _classify_profile_qualifications(
    sections: dict[str, str],
) -> None:
    """
    A candidate profile can mix mandatory and optional criteria.
    Only explicitly optional items are moved to preferred qualifications.
    """
    required_text = sections.get("required_qualifications", "")
    if not required_text:
        return

    required_items = []
    preferred_items = []

    for item in _split_items(required_text):
        lowered = item.lower()

        if any(cue in lowered for cue in _PREFERRED_CUES):
            preferred_items.append(item)
        else:
            required_items.append(item)

    sections["required_qualifications"] = "\n".join(required_items).strip()

    if preferred_items:
        existing = sections.get("preferred_qualifications", "")
        sections["preferred_qualifications"] = "\n".join(
            part
            for part in (existing, "\n".join(preferred_items))
            if part.strip()
        ).strip()


def parse_job_description(job_description: str) -> dict[str, Any]:
    cleaned_text = clean_job_description(job_description)

    if not cleaned_text:
        return {
            "cleaned_text": "",
            "sections": {},
            "recognized_sections": [],
        }

    collected: dict[str, list[str]] = {"overview": []}
    current_section = "overview"
    recognized: set[str] = set()

    for raw_line in cleaned_text.splitlines():
        line = _MARKDOWN_PREFIX.sub("", raw_line).strip()
        if not line:
            continue

        standalone = _heading_from_line(line)
        if standalone:
            current_section = standalone
            collected.setdefault(current_section, [])
            recognized.add(current_section)
            continue

# Preserve a bullet immediately under a Markdown heading for compatibility.
# For ordinary content lines, remove list markers.
        if not re.match(r"^\s*-\s+", raw_line) or not recognized:
            line = _BULLET_PREFIX.sub("", line)
        headings = _find_inline_headings(line)

        if not headings:
            collected.setdefault(current_section, []).append(line)
            continue

        cursor = 0

        for start, end, section in headings:
            prefix = line[cursor:start].strip(" \t|")

            if prefix:
                collected.setdefault(current_section, []).append(prefix)

            current_section = section
            collected.setdefault(current_section, [])
            recognized.add(section)
            cursor = end

        suffix = line[cursor:].strip(" \t|")
        if suffix:
            collected.setdefault(current_section, []).append(suffix)

    sections = {
        name: "\n".join(parts).strip()
        for name, parts in collected.items()
        if any(part.strip() for part in parts)
    }

    if not recognized:
        sections = {"overview": cleaned_text}

    _classify_profile_qualifications(sections)

    order = (
        "overview",
        "responsibilities",
        "required_qualifications",
        "preferred_qualifications",
        "skills",
        "education",
    )

    ordered_sections = {
        name: sections[name]
        for name in order
        if sections.get(name)
    }

    return {
        "cleaned_text": cleaned_text,
        "sections": ordered_sections,
        "recognized_sections": list(ordered_sections.keys()),
    }
