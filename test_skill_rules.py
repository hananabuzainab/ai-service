
from app.skill_rules import (
    refine_resume_skills,
    refine_job_skills,
    _canonical_parts,
)


def test_aliases():
    assert _canonical_parts("JS") == ["javascript"]
    assert _canonical_parts("Postgres") == ["postgresql"]
    assert _canonical_parts("NodeJS") == ["node.js"]


def test_parentheses():
    assert _canonical_parts("SQL (Postgres)") == [
        "sql",
        "postgresql"
    ]


def test_split_skills():
    assert _canonical_parts("HTML/CSS") == ["html", "css"]
    assert _canonical_parts("CI/CD") == ["ci/cd"]


def test_gitlab_ci_cd_alias():
    assert _canonical_parts("GitLab CI/CD") == ["gitlab ci"]


def test_implied_skills():
    skills = [
        {
            "name": "Django",
            "category": "frameworks",
            "confidence_score": 0.95
        }
    ]

    result = refine_resume_skills(skills)
    names = [skill["name"] for skill in result]

    assert "django" in names
    assert "python" in names


def test_explicit_score_is_preserved():
    skills = [
        {
            "name": "Django",
            "category": "frameworks",
            "confidence_score": 0.95
        },
        {
            "name": "Python",
            "category": "languages",
            "confidence_score": 0.40
        }
    ]

    result = refine_resume_skills(skills)

    python = next(
        skill for skill in result
        if skill["name"] == "python"
    )

    assert python["confidence_score"] == 0.40


def test_string_score():
    skills = [
        {
            "name": "Python",
            "category": "languages",
            "confidence_score": "0.85"
        }
    ]

    result = refine_resume_skills(skills)

    assert result[0]["confidence_score"] == 0.85


def test_job_importance():
    skills = [
        {
            "name": "PostgreSQL",
            "category": "databases",
            "importance": 0.90
        }
    ]

    result = refine_job_skills(skills)

    sql = next(
        skill for skill in result
        if skill["name"] == "sql"
    )

    assert sql["importance"] == 0.90

def test_canonical_parts_rejects_non_string_names():
    from app.skill_rules import _canonical_parts

    assert _canonical_parts(None) == []
    assert _canonical_parts(123) == []
    assert _canonical_parts([]) == []


def test_canonical_parts_keeps_tcp_ip():
    from app.skill_rules import _canonical_parts

    assert _canonical_parts("TCP/IP") == ["tcp/ip"]


def test_canonical_parts_keeps_ci_cd():
    from app.skill_rules import _canonical_parts

    assert _canonical_parts("CI/CD") == ["ci/cd"]


def test_celery_category_is_frameworks():
    from app.skill_rules import CATEGORY

    assert CATEGORY["celery"] == "frameworks"    
