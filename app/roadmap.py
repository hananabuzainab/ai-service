import re

from app.llm import ask_llm_json
from app.resources import get_resources
from prompts.generate_roadmap import GENERATE_ROADMAP_PROMPT

MAX_STEPS = 6
MAX_TOPICS = 5


def _to_float(value, default=0.0):
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def sort_skills(skills):
    return sorted(skills, key=lambda s: _to_float(s.get("importance")), reverse=True)


def _clean_topics(value):
    if not isinstance(value, list):
        return []
    topics = [str(v).strip()[:120] for v in value if str(v).strip()]
    return topics[:MAX_TOPICS]


def build_message(job_title, known_skills, skill):
    known = ", ".join(known_skills) if known_skills else "(none)"
    return (
        f"<job_title>\n{job_title}\n</job_title>\n"
        f"<known_skills>\n{known}\n</known_skills>\n"
        f"<skill>\nname: {skill['name']}\n"
        f"category: {skill.get('category', 'other')}\n"
        f"importance: {skill.get('importance')}\n</skill>"
    )


def clean_roadmap(raw, skill, priority):
    raw_steps = raw.get("steps")
    if not isinstance(raw_steps, list):
        raise ValueError("Roadmap has no steps")

    steps = []
    for item in raw_steps[:MAX_STEPS]:
        if not isinstance(item, dict):
            continue
        title = str(item.get("title", "")).strip()
        title = re.sub(r"^\s*week\s*\d+\s*[:\-–]\s*", "", title, flags=re.IGNORECASE)
        title = title[:120]
        if not title:
            continue
        steps.append({
            "week": len(steps) + 1,
            "title": title,
            "topics": _clean_topics(item.get("topics")),
        })

    if not steps:
        raise ValueError("Roadmap has no valid steps")

    weeks = len(steps)
    resources = [{"title": r["title"], "url": r["url"]} for r in get_resources(skill["name"])]

    return {
        "skill_id": skill.get("id"),
        "skill_name": skill["name"],
        "category": skill.get("category", "other"),
        "importance": _to_float(skill.get("importance")),
        "priority": priority,
        "title": f"Learning roadmap: {skill['name']}",
        "estimated_duration": f"{weeks} week" + ("" if weeks == 1 else "s"),
        "steps": steps,
        "resources": resources,
    }


def generate_roadmap(skill, priority, job_title, known_skills):
    message = build_message(job_title, known_skills, skill)
    raw = ask_llm_json(GENERATE_ROADMAP_PROMPT, message)
    return clean_roadmap(raw, skill, priority)