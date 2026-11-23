
import re

from app.skill_catalog import SKILL_ALIASES


def _make_pattern(alias: str) -> re.Pattern:
    """Match an alias without matching inside a larger word."""
    escaped = re.escape(alias.strip())

    return re.compile(
        rf"(?<!\w){escaped}(?!\w)",
        re.IGNORECASE,
    )


_COMPILED_ALIASES = [
    (canonical, alias, _make_pattern(alias))
    for canonical, aliases in SKILL_ALIASES.items()
    for alias in sorted(aliases, key=len, reverse=True)
]

# Prefer longer aliases before shorter overlapping aliases.
_COMPILED_ALIASES.sort(
    key=lambda item: len(item[1]),
    reverse=True,
)


def _clean_text(text: str) -> str:
    """Normalize common invisible characters from PDF extraction."""
    return (
        text.replace("\u200b", "")
        .replace("\u200c", "")
        .replace("\u200d", "")
        .replace("\ufeff", "")
        .strip()
    )


def _get_line(text: str, start: int, end: int) -> str:
    """Return the line containing a match."""
    line_start = text.rfind("\n", 0, start) + 1
    line_end = text.find("\n", end)

    if line_end == -1:
        line_end = len(text)

    return _clean_text(text[line_start:line_end])


def _is_probably_skill_list(text: str) -> bool:
    """Heuristically detect comma-separated catalog-style skill lists."""
    separators = sum(text.count(char) for char in (",", "|", ";"))

    action_words = re.search(
        r"\b("
        r"built|developed|implemented|designed|deployed|"
        r"created|maintained|evaluated|trained|used|"
        r"worked|managed|led|experience|experienced|"
        r"proficient|responsible"
        r")\b",
        text,
        re.IGNORECASE,
    )

    return separators >= 2 and action_words is None


def _precise_evidence(
    line: str,
    alias_pattern: re.Pattern,
) -> str:
    """
    Extract a concise text snippet around the skill mention.

    For skill lists, return the individual list item.
    For descriptive text, preserve the sentence as context.
    """
    if not line:
        return ""

    # A line may contain a category label before a colon:
    # "Languages: JavaScript, Java, Python, SQL"
    if ":" in line:
        label, value = line.split(":", 1)

        if len(label.strip()) <= 60 and alias_pattern.search(value):
            line = value.strip()

    if _is_probably_skill_list(line):
        items = re.split(r"[,|;]", line)

        for item in items:
            item = item.strip()

            if alias_pattern.search(item):
                return item[:240]

    # Keep sentence-level context for descriptive resume statements.
    sentences = re.split(r"(?<=[.!?])\s+", line)

    for sentence in sentences:
        if alias_pattern.search(sentence):
            return sentence.strip()[:240]

    return line[:240]


def extract_skills(text: str) -> list[dict]:
    """
    Extract known catalog skills and concise text evidence.

    A detected mention is not proof of proficiency or experience.
    """
    if not isinstance(text, str) or not text.strip():
        return []

    text = _clean_text(text)
    found = {}

    for canonical, alias, pattern in _COMPILED_ALIASES:
        if canonical in found:
            continue

        match = pattern.search(text)

        if not match:
            continue

        line = _get_line(text, match.start(), match.end())
        evidence = _precise_evidence(line, pattern)

        found[canonical] = {
            "skill": canonical,
            "matched_alias": match.group(0),
            "evidence": evidence,
        }

    return sorted(
        found.values(),
        key=lambda item: item["skill"].lower(),
    )
