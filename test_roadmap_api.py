
from fastapi.testclient import TestClient

from app import main


client = TestClient(main.app)


def make_roadmap(skill, priority):
    return {
        "skill_id": skill.get("id"),
        "skill_name": skill["name"],
        "category": skill.get("category", "other"),
        "importance": skill.get("importance") or 0.0,
        "priority": priority,
        "title": f"Learning roadmap: {skill['name']}",
        "estimated_duration": "2 weeks",
        "steps": [
            {
                "week": 1,
                "title": "Learn the fundamentals",
                "topics": [
                    "Core concepts",
                    "Basic syntax",
                    "Practical examples",
                ],
            },
            {
                "week": 2,
                "title": "Build a small project",
                "topics": [
                    "Project setup",
                    "Implementation",
                    "Testing",
                ],
            },
        ],
        "resources": [
            {
                "title": "Official documentation",
                "url": "https://example.com/docs",
            }
        ],
    }


def test_empty_missing_skills():
    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [
                {"name": "python"}
            ],
            "missing_skills": [],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"roadmaps": []}


def test_generate_roadmap_success(monkeypatch):
    def fake_generate(skill, priority, job_title, known):
        return make_roadmap(skill, priority)

    monkeypatch.setattr(
        main,
        "generate_roadmap",
        fake_generate,
    )

    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [
                {"name": "python"}
            ],
            "missing_skills": [
                {
                    "id": 1,
                    "name": "django",
                    "category": "frameworks",
                    "importance": 0.9,
                }
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert len(data["roadmaps"]) == 1
    assert data["roadmaps"][0]["skill_name"] == "django"
    assert data["roadmaps"][0]["priority"] == 1
    assert len(data["roadmaps"][0]["steps"]) == 2


def test_maximum_five_roadmaps(monkeypatch):
    generated_skills = []

    def fake_generate(skill, priority, job_title, known):
        generated_skills.append(skill["name"])
        return make_roadmap(skill, priority)

    monkeypatch.setattr(
        main,
        "generate_roadmap",
        fake_generate,
    )

    missing_skills = [
        {
            "id": i,
            "name": f"skill-{i}",
            "category": "other",
            "importance": i / 10,
        }
        for i in range(1, 8)
    ]

    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [],
            "missing_skills": missing_skills,
        },
    )

    assert response.status_code == 200
    assert len(response.json()["roadmaps"]) == 5
    assert len(generated_skills) == 5


def test_roadmaps_sorted_by_importance(monkeypatch):
    generated_skills = []

    def fake_generate(skill, priority, job_title, known):
        generated_skills.append(
            (skill["name"], priority)
        )
        return make_roadmap(skill, priority)

    monkeypatch.setattr(
        main,
        "generate_roadmap",
        fake_generate,
    )

    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [],
            "missing_skills": [
                {
                    "id": 1,
                    "name": "sql",
                    "category": "databases",
                    "importance": 0.5,
                },
                {
                    "id": 2,
                    "name": "django",
                    "category": "frameworks",
                    "importance": 0.9,
                },
                {
                    "id": 3,
                    "name": "docker",
                    "category": "cloud_devops",
                    "importance": 0.7,
                },
            ],
        },
    )

    assert response.status_code == 200

    assert generated_skills == [
        ("django", 1),
        ("docker", 2),
        ("sql", 3),
    ]



def test_roadmap_generation_failure_continues_with_remaining_skills(monkeypatch):
    generated_skills = []

    def fake_generate(skill, priority, job_title, known):
        generated_skills.append((skill["name"], priority))

        if skill["name"] == "django":
            raise RuntimeError("Gemini failed")

        return make_roadmap(skill, priority)

    monkeypatch.setattr(
        main,
        "generate_roadmap",
        fake_generate,
    )

    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [],
            "missing_skills": [
                {
                    "id": 1,
                    "name": "django",
                    "category": "frameworks",
                    "importance": 0.9,
                },
                {
                    "id": 2,
                    "name": "docker",
                    "category": "cloud_devops",
                    "importance": 0.8,
                },
                {
                    "id": 3,
                    "name": "sql",
                    "category": "databases",
                    "importance": 0.7,
                },
            ],
        },
    )

    assert response.status_code == 200

    data = response.json()

    assert generated_skills == [
        ("django", 1),
        ("docker", 2),
        ("sql", 3),
    ]

    assert len(data["roadmaps"]) == 2

    assert [
        item["skill_name"]
        for item in data["roadmaps"]
    ] == ["docker", "sql"]

    assert [
        item["priority"]
        for item in data["roadmaps"]
    ] == [2, 3]


def test_all_roadmap_generations_fail(monkeypatch):
    def fake_generate(*args):
        raise RuntimeError("Gemini failed")

    monkeypatch.setattr(
        main,
        "generate_roadmap",
        fake_generate,
    )

    response = client.post(
        "/v1/generate-roadmap",
        json={
            "job_title": "Backend Developer",
            "matching_skills": [],
            "missing_skills": [
                {
                    "id": 1,
                    "name": "django",
                    "category": "frameworks",
                    "importance": 0.9,
                },
                {
                    "id": 2,
                    "name": "docker",
                    "category": "cloud_devops",
                    "importance": 0.8,
                },
            ],
        },
    )

    assert response.status_code == 200
    assert response.json() == {"roadmaps": []}
