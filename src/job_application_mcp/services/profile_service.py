from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_application_mcp.database.models import Profile
from job_application_mcp.models.profile import ProfileIn, ProfileOut


def _row_to_out(row: Profile) -> ProfileOut:
    def _load(col):
        return json.loads(col) if col else None

    return ProfileOut(
        id=row.id,
        name=row.name,
        location=row.location,
        education=_load(row.education),
        skills=_load(row.skills),
        projects=_load(row.projects),
        experience=_load(row.experience),
        research_interests=_load(row.research_interests),
        certifications=_load(row.certifications),
        achievements=_load(row.achievements),
        preferences=_load(row.preferences),
    )


async def get_or_create_profile(session: AsyncSession) -> Profile:
    """This is a single-user MCP server: there is exactly one profile row."""
    result = await session.execute(select(Profile).limit(1))
    profile = result.scalar_one_or_none()
    if profile is None:
        profile = Profile()
        session.add(profile)
        await session.flush()
    return profile


async def get_profile(session: AsyncSession) -> ProfileOut:
    profile = await get_or_create_profile(session)
    return _row_to_out(profile)


async def update_profile(session: AsyncSession, data: ProfileIn) -> ProfileOut:
    """Partial update: only fields the caller actually set are changed.

    Never fabricates or infers values — every field written here came from
    an explicit argument the caller (the user, via Claude) supplied.
    """
    profile = await get_or_create_profile(session)
    updates = data.model_dump(exclude_unset=True)

    simple_fields = {"name", "location"}
    json_fields = {
        "education",
        "skills",
        "projects",
        "experience",
        "research_interests",
        "certifications",
        "achievements",
        "preferences",
    }

    for field, value in updates.items():
        if field in simple_fields:
            setattr(profile, field, value)
        elif field in json_fields:
            serializable = [
                item.model_dump() if hasattr(item, "model_dump") else item for item in value
            ] if isinstance(value, list) else value
            setattr(profile, field, json.dumps(serializable))

    await session.flush()
    return _row_to_out(profile)


async def profile_summary(session: AsyncSession) -> str:
    """A concise summary built only from stored fields — no invented content."""
    profile = await get_profile(session)
    parts: list[str] = []
    if profile.name:
        parts.append(profile.name)
    if profile.education:
        latest = profile.education[0]
        degree_bits = " ".join(
            b for b in [latest.degree, "in", latest.field_of_study] if b
        ) if latest.field_of_study else (latest.degree or "")
        if degree_bits:
            parts.append(f"{degree_bits} at {latest.institution}".strip())
    if profile.skills:
        parts.append("Skills: " + ", ".join(profile.skills[:12]))
    if not parts:
        return "Profile is empty. Use profile_update to add information before requesting a summary."
    return ". ".join(parts) + "."
