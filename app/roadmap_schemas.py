from pydantic import BaseModel, Field


class MissingSkill(BaseModel):
    id: int | None = None
    name: str = Field(min_length=1, max_length=45)
    category: str = "other"
    importance: float | None = None


class KnownSkill(BaseModel):
    name: str = Field(min_length=1, max_length=45)


class RoadmapRequest(BaseModel):
    job_title: str = Field(min_length=1, max_length=200)
    matching_skills: list[KnownSkill] = Field(default_factory=list, max_length=100)
    missing_skills: list[MissingSkill] = Field(default_factory=list, max_length=100)


class RoadmapStep(BaseModel):
    week: int
    title: str
    topics: list[str]


class RoadmapResource(BaseModel):
    title: str
    url: str


class Roadmap(BaseModel):
    skill_id: int | None
    skill_name: str
    category: str
    importance: float
    priority: int
    title: str
    estimated_duration: str
    steps: list[RoadmapStep]
    resources: list[RoadmapResource]


class RoadmapsResponse(BaseModel):
    roadmaps: list[Roadmap]