
import pytest

from app import roadmap


def test_sort_skills_by_importance():
    skills = [
        {"name": "SQL", "importance": 0.5},
        {"name": "Django", "importance": 0.9},
        {"name": "Docker", "importance": 0.7},
    ]

    result = roadmap.sort_skills(skills)

    assert [s["name"] for s in result] == [
        "Django",
        "Docker",
        "SQL",
    ]


def test_sort_skills_invalid_importance():
    skills = [
        {"name": "Python", "importance": "invalid"},
        {"name": "Django", "importance": 0.8},
        {"name": "SQL", "importance": None},
    ]

    result = roadmap.sort_skills(skills)

    assert result[0]["name"] == "Django"


def test_clean_topics_limits_to_five():
    topics = [
        "Topic 1",
        "Topic 2",
        "Topic 3",
        "Topic 4",
        "Topic 5",
        "Topic 6",
    ]

    result = roadmap._clean_topics(topics)

    assert len(result) == 5
    assert result[-1] == "Topic 5"


def test_clean_topics_invalid_input():
    assert roadmap._clean_topics("Python") == []
    assert roadmap._clean_topics(None) == []


def test_clean_topics_removes_empty_values():
    result = roadmap._clean_topics([
        " Python ",
        "",
        " Django ",
        "   ",
    ])

    assert result == ["Python", "Django"]


def test_clean_roadmap_success(monkeypatch):
    monkeypatch.setattr(
        roadmap,
        "get_resources",
        lambda skill_name: [
            {
                "title": "Official documentation",
                "url": "https://example.com",
            }
        ],
    )

    skill = {
        "id": 1,
        "name": "Django",
        "category": "frameworks",
        "importance": 0.9,
    }

    raw = {
        "steps": [
            {
                "title": "Learn Django fundamentals",
                "topics": [
                    "Models",
                    "Views",
                    "URLs",
                ],
            },
            {
                "title": "Build a Django project",
                "topics": [
                    "Project setup",
                    "Database",
                    "Testing",
                ],
            },
        ]
    }

    result = roadmap.clean_roadmap(raw, skill, 1)

    assert result["skill_name"] == "Django"
    assert result["priority"] == 1
    assert result["importance"] == 0.9
    assert result["estimated_duration"] == "2 weeks"
    assert len(result["steps"]) == 2
    assert result["steps"][0]["week"] == 1
    assert result["steps"][1]["week"] == 2
    assert result["resources"][0]["title"] == "Official documentation"


def test_clean_roadmap_limits_steps(monkeypatch):
    monkeypatch.setattr(
        roadmap,
        "get_resources",
        lambda skill_name: [],
    )

    skill = {
        "name": "Python",
        "importance": 0.8,
    }

    raw = {
        "steps": [
            {"title": f"Step {i}", "topics": []}
            for i in range(1, 9)
        ]
    }

    result = roadmap.clean_roadmap(raw, skill, 1)

    assert len(result["steps"]) == roadmap.MAX_STEPS
    assert result["steps"][-1]["week"] == roadmap.MAX_STEPS


def test_clean_roadmap_skips_invalid_steps(monkeypatch):
    monkeypatch.setattr(
        roadmap,
        "get_resources",
        lambda skill_name: [],
    )

    skill = {
        "name": "Python",
        "importance": 0.8,
    }

    raw = {
        "steps": [
            None,
            {"title": "", "topics": []},
            {"title": "Valid step", "topics": ["Basics"]},
        ]
    }

    result = roadmap.clean_roadmap(raw, skill, 1)

    assert len(result["steps"]) == 1
    assert result["steps"][0]["week"] == 1
    assert result["steps"][0]["title"] == "Valid step"


def test_clean_roadmap_missing_steps():
    with pytest.raises(ValueError, match="no steps"):
        roadmap.clean_roadmap(
            {},
            {"name": "Python"},
            1,
        )


def test_clean_roadmap_no_valid_steps(monkeypatch):
    monkeypatch.setattr(
        roadmap,
        "get_resources",
        lambda skill_name: [],
    )

    with pytest.raises(ValueError, match="no valid steps"):
        roadmap.clean_roadmap(
            {
                "steps": [
                    None,
                    {"title": "", "topics": []},
                ]
            },
            {"name": "Python"},
            1,
        )


def test_generate_roadmap_calls_llm_and_cleans(monkeypatch):
    monkeypatch.setattr(
        roadmap,
        "ask_llm_json",
        lambda prompt, message: {
            "steps": [
                {
                    "title": "Learn Python basics",
                    "topics": ["Variables", "Functions"],
                }
            ]
        },
    )

    monkeypatch.setattr(
        roadmap,
        "get_resources",
        lambda skill_name: [],
    )

    skill = {
        "id": 5,
        "name": "Python",
        "category": "languages",
        "importance": 0.95,
    }

    result = roadmap.generate_roadmap(
        skill,
        1,
        "Backend Developer",
        ["SQL", "Git"],
    )

    assert result["skill_name"] == "Python"
    assert result["priority"] == 1
    assert len(result["steps"]) == 1

