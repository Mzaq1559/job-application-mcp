from __future__ import annotations

from job_application_mcp.database.database import session_scope
from job_application_mcp.mcp_app import mcp
from job_application_mcp.models.profile import ProfileIn
from job_application_mcp.services import profile_service


@mcp.tool()
async def profile_get() -> dict:
    """Return the user's stored professional profile (name, education, skills,
    projects, experience, research interests, certifications, achievements,
    preferences). Read-only — safe to call any time context is needed."""
    async with session_scope() as session:
        return (await profile_service.get_profile(session)).model_dump()


@mcp.tool()
async def profile_update(
    name: str | None = None,
    location: str | None = None,
    education: list[dict] | None = None,
    skills: list[str] | None = None,
    projects: list[dict] | None = None,
    experience: list[dict] | None = None,
    research_interests: list[str] | None = None,
    certifications: list[str] | None = None,
    achievements: list[str] | None = None,
    preferences: dict | None = None,
) -> dict:
    """Update the stored profile. Only pass fields you want to change — omitted
    fields are left untouched (this is a partial update, not a replace).
    Every value must come from the user directly; never invent or infer
    profile content on their behalf."""
    payload = ProfileIn(
        name=name,
        location=location,
        education=education,
        skills=skills,
        projects=projects,
        experience=experience,
        research_interests=research_interests,
        certifications=certifications,
        achievements=achievements,
        preferences=preferences,
    )
    async with session_scope() as session:
        return (await profile_service.update_profile(session, payload)).model_dump()


@mcp.tool()
async def profile_summary() -> str:
    """Generate a short, factual professional summary built only from stored
    profile fields — no embellishment or invented claims."""
    async with session_scope() as session:
        return await profile_service.profile_summary(session)
