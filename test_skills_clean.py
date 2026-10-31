
import math
import pytest

from app.skills_clean import (
    clean_resume_skills,
    clean_job_skills,
    _normalize_score,
    _normalize_name,
    limit_text,
)


def test_resume_skills_normalization():
    skills = [
        {
            "name": " Python ",
            "category": "languages",
            "confidence_score": 0.9
        }
    ]

    result = clean_resume_skills(skills)

    assert result == [
        {
            "name": "python",
            "category": "languages",
            "confidence_score": 0.9
        }
    ]


def test_duplicate_skills_keep_highest_score():
    skills = [
        {
            "name": "Python",
            "category": "languages",
            "confidence_score": 0.6
        },
        {
            "name": "python",
            "category": "languages",
            "confidence_score": 0.9
        }
    ]

    result = clean_resume_skills(skills)

    assert len(result) == 1
    assert result[0]["confidence_score"] == 0.9


def test_invalid_score():
    assert _normalize_score("invalid") is None
    assert _normalize_score(float("inf")) is None
    assert _normalize_score(float("-inf")) is None
    assert _normalize_score(float("nan")) is None
    assert _normalize_score(True) is None


def test_score_boundaries():
    assert _normalize_score(1.5) == 1.0
    assert _normalize_score(-0.5) == 0.0
    assert _normalize_score("0.85") == 0.85


def test_invalid_category_becomes_other():
    skills = [
        {
            "name": "Python",
            "category": "unknown_category",
            "confidence_score": 0.9
        }
    ]

    result = clean_resume_skills(skills)

    assert result[0]["category"] == "other"


def test_long_skill_name_is_rejected():
    name = "a" * 50

    assert _normalize_name(name) == ""


def test_invalid_skills_input():
    with pytest.raises(ValueError):
        clean_resume_skills("python")


def test_job_importance_default():
    skills = [
        {
            "name": "Django",
            "category": "frameworks",
            "importance": None
        }
    ]

    result = clean_job_skills(skills)

    assert result[0]["importance"] == 0.5


def test_limit_text():
    text = "A" * 70000

    result = limit_text(text)

    assert len(result.encode("utf-8")) <= 65535


def test_limit_text_preserves_arabic():
    text = "مرحبا " * 20000

    result = limit_text(text)

    assert len(result.encode("utf-8")) <= 65535
