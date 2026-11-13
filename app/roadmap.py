import re

from app.llm import ask_llm_json
from app.resources import get_resources
from prompts.generate_roadmap import GENERATE_ROADMAP_PROMPT

MAX_STEPS = 6
MAX_TOPICS = 5
MIN_TOPICS = 3


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sort_skills(skills):
    return sorted(
        skills,
        key=lambda skill: _to_float(skill.get("importance")),
        reverse=True,
    )


def _clean_topics(value):
    if not isinstance(value, list):
        return []

    topics = []

    for item in value:
        if not isinstance(item, str):
            continue

        topic = item.strip()

        if topic:
            topics.append(topic[:120])

        if len(topics) >= MAX_TOPICS:
            break

    return topics


def build_message(job_title, known_skills, skill, other_missing_skills=None):
    known = ", ".join(known_skills) if known_skills else "(none)"

    other_missing = (
        ", ".join(other_missing_skills)
        if other_missing_skills
        else "(none)"
    )

    return (
    f"<job_title>\n{job_title}\n</job_title>\n"
    f"<known_skills>\n{known}\n</known_skills>\n"
    f"<other_missing_skills>\n{other_missing}\n</other_missing_skills>\n"
    f"<skill>\n"
    f"name: {skill['name']}\n"
    f"category: {skill.get('category', 'other')}\n"
    f"importance: {skill.get('importance')}\n"
    f"</skill>"
)


def clean_roadmap(raw, skill, priority):
    if not isinstance(raw, dict):
        raise ValueError("Invalid roadmap response")

    raw_steps = raw.get("steps")

    if not isinstance(raw_steps, list):
        raise ValueError("Roadmap has no steps")

    steps = []

    for item in raw_steps:
        if not isinstance(item, dict):
            continue

        title = str(item.get("title", "")).strip()

        title = re.sub(
            r"^\s*week\s+\d+\s*[:\-–]\s*",
            "",
            title,
            flags=re.IGNORECASE,
        )

        title = title[:120]

        topics = _clean_topics(item.get("topics"))

        if not title or len(topics) < MIN_TOPICS:
            continue

        steps.append({
            "week": len(steps) + 1,
            "title": title,
            "topics": topics,
        })

        if len(steps) >= MAX_STEPS:
            break

    if not steps:
        raise ValueError("Roadmap has no valid steps")

    weeks = len(steps)

    resources = [
        {
            "title": resource["title"],
            "url": resource["url"],
        }
        for resource in get_resources(skill["name"])
    ]

    return {
        "skill_id": skill.get("id"),
        "skill_name": skill["name"],
        "category": skill.get("category", "other"),
        "importance": _to_float(skill.get("importance")),
        "priority": priority,
        "title": f"Learning roadmap: {skill['name']}",
        "estimated_duration": (
            f"{weeks} week" if weeks == 1 else f"{weeks} weeks"
        ),
        "steps": steps,
        "resources": resources,
    }


def _is_complete(roadmap):
    steps = roadmap["steps"]
    importance = roadmap["importance"]

    minimum = (
        4 if importance >= 0.8
        else 3 if importance >= 0.5
        else 2
    )

    final_title = steps[-1]["title"].lower()

    has_practical_final_step = any(
        term in final_title
        for term in (
    "project",
    "application",
    "exercise",
    "case study",
    "task",
    "simulation",
    "implementation",
)
    )

    return len(steps) >= minimum and has_practical_final_step


def generate_roadmap(
    skill,
    priority,
    job_title,
    known_skills,
    other_missing_skills=None,
):
    message = build_message(
        job_title,
        known_skills,
        skill,
        other_missing_skills,
    )

    for attempt in range(2):
        raw = ask_llm_json(GENERATE_ROADMAP_PROMPT, message)
        roadmap = clean_roadmap(raw, skill, priority)

        if _is_complete(roadmap):
            return roadmap

    raise ValueError(
        f"Incomplete roadmap generated for skill '{skill['name']}'"
    )