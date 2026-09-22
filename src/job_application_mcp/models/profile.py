from __future__ import annotations

from pydantic import BaseModel, Field


class EducationEntry(BaseModel):
    institution: str
    degree: str | None = None
    field_of_study: str | None = None
    start_date: str | None = None
    end_date: str | None = None
    gpa: str | None = None
    notes: str | None = None


class ExperienceEntry(BaseModel):
    organization: str
    role: str
    start_date: str | None = None
    end_date: str | None = None
    description: str | None = None


class ProjectEntry(BaseModel):
    name: str
    description: str | None = None
    technologies: list[str] = Field(default_factory=list)
    url: str | None = None


class ProfileIn(BaseModel):
    """Fields accepted by profile_update. All optional — partial updates are merged."""

    name: str | None = None
    location: str | None = None
    education: list[EducationEntry] | None = None
    skills: list[str] | None = None
    projects: list[ProjectEntry] | None = None
    experience: list[ExperienceEntry] | None = None
    research_interests: list[str] | None = None
    certifications: list[str] | None = None
    achievements: list[str] | None = None
    preferences: dict | None = None


class ProfileOut(ProfileIn):
    id: str
