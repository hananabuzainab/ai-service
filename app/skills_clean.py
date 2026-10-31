
import logging
import math


logger = logging.getLogger("skills_clean")


CATEGORIES = [
    "languages",
    "frameworks",
    "databases",
    "cloud_devops",
    "ml_data",
    "tools",
    "other",
]


LOWERCASE_NAMES = True

MAX_SKILLS = 500
MAX_NAME_LENGTH = 45
MAX_TEXT_BYTES = 65535

DEFAULT_IMPORTANCE = 0.5


def _normalize_name(value):
    """
    Normalize a skill name.

    - Remove extra whitespace.
    - Convert to lowercase when configured.
    - Reject empty or excessively long names.
    """

    if not isinstance(value, str):
        return ""

    name = " ".join(value.split())

    if LOWERCASE_NAMES:
        name = name.lower()

    if not name:
        return ""

    if len(name) > MAX_NAME_LENGTH:
        logger.warning(
            "Skill name rejected because it exceeds "
            "the maximum length: %s characters",
            len(name)
        )
        return ""

    return name


def _normalize_score(value):
    """
    Normalize a score to a float between 0 and 1.

    Invalid values return None.
    """

    if isinstance(value, bool):
        return None

    if isinstance(value, str):
        try:
            value = float(value.strip())
        except ValueError:
            return None

    if not isinstance(value, (int, float)):
        return None

    value = float(value)

    if not math.isfinite(value):
        return None

    value = min(max(value, 0.0), 1.0)

    return round(value, 2)


def _merge_skills(raw_skills, score_field):
    """
    Normalize skills and merge duplicates.

    When the same skill appears more than once,
    keep the highest valid score.
    """

    if not isinstance(raw_skills, list):
        raise ValueError(
            "Expected skills to be a list."
        )

    merged = {}

    for item in raw_skills:

        if not isinstance(item, dict):
            logger.warning(
                "Skipping invalid skill item: expected a dictionary."
            )
            continue

        name = _normalize_name(item.get("name"))

        if not name:
            continue

        category = str(
            item.get("category", "")
        ).strip().lower()

        if category not in CATEGORIES:
            category = "other"

        score = _normalize_score(
            item.get(score_field)
        )

        if name not in merged:

            if len(merged) >= MAX_SKILLS:
                logger.warning(
                    "Maximum number of skills reached: %s",
                    MAX_SKILLS
                )
                continue

            merged[name] = {
                "category": category,
                "score": score
            }

            continue

        old_score = merged[name]["score"]

        old_rank = (
            -1 if old_score is None else old_score
        )

        new_rank = (
            -1 if score is None else score
        )

        if new_rank > old_rank:
            merged[name] = {
                "category": category,
                "score": score
            }

    return merged


def clean_resume_skills(raw_skills):
    """
    Clean extracted resume skills.

    Each skill contains:
    - name
    - category
    - confidence_score
    """

    merged = _merge_skills(
        raw_skills,
        "confidence_score"
    )

    cleaned = []

    for name, info in merged.items():

        cleaned.append({
            "name": name,
            "category": info["category"],
            "confidence_score": info["score"]
        })

    return cleaned


def clean_job_skills(raw_skills):
    """
    Clean extracted job description skills.

    Each skill contains:
    - name
    - category
    - importance
    """

    merged = _merge_skills(
        raw_skills,
        "importance"
    )

    cleaned = []

    for name, info in merged.items():

        importance = info["score"]

        if importance is None:
            importance = DEFAULT_IMPORTANCE

            logger.warning(
                "Missing or invalid importance score for skill '%s'. "
                "Using default value: %s",
                name,
                DEFAULT_IMPORTANCE
            )

        cleaned.append({
            "name": name,
            "category": info["category"],
            "importance": importance
        })

    return cleaned


def limit_text(text):
    """
    Limit returned text by UTF-8 byte size.

    This function is intended to limit the text
    returned in the API response.
    """

    if not isinstance(text, str):
        return ""

    encoded = text.encode("utf-8")

    if len(encoded) <= MAX_TEXT_BYTES:
        return text

    return encoded[:MAX_TEXT_BYTES].decode(
        "utf-8",
        errors="ignore"
    )
