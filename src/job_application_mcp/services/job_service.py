from __future__ import annotations

from datetime import datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_application_mcp.database.models import Job
from job_application_mcp.models.job import JobIn

VALID_STATUSES = {
    "saved",
    "analyzing",
    "ready_to_apply",
    "applied",
    "screening",
    "interview",
    "offer",
    "rejected",
    "withdrawn",
    "closed",
}


async def create_job(session: AsyncSession, data: JobIn) -> Job:
    job = Job(**data.model_dump())
    session.add(job)
    await session.flush()
    return job


async def get_job(session: AsyncSession, job_id: str) -> Job | None:
    return await session.get(Job, job_id)


async def list_jobs(
    session: AsyncSession,
    *,
    status: str | None = None,
    company: str | None = None,
) -> list[Job]:
    stmt = select(Job)
    if status:
        stmt = stmt.where(Job.status == status)
    if company:
        stmt = stmt.where(Job.company.ilike(f"%{company}%"))
    result = await session.execute(stmt.order_by(Job.created_at.desc()))
    return list(result.scalars().all())


async def find_possible_duplicate(session: AsyncSession, data: JobIn) -> Job | None:
    """Duplicate check by URL first, then company+title, before a new job/application is created."""
    if data.source_url:
        result = await session.execute(select(Job).where(Job.source_url == data.source_url))
        existing = result.scalar_one_or_none()
        if existing:
            return existing

    result = await session.execute(
        select(Job).where(Job.company.ilike(data.company), Job.title.ilike(data.title))
    )
    return result.scalars().first()


def analyze_job(job_description: str, requirements: str | None, profile_skills: list[str]) -> dict:
    """Transparent requirement/keyword comparison against stored profile skills.

    This is a deterministic, explainable baseline. Deeper natural-language
    analysis (matching_requirements / missing_requirements with reasoning)
    belongs in an AI-assisted layer (services/ai_service.py) that must follow
    the no-fabrication prompt rules in prompts/job_analysis.py — not
    implemented here to keep this function auditable and dependency-free.
    """
    text = f"{job_description}\n{requirements or ''}".lower()
    matching = [s for s in profile_skills if s.lower() in text]
    missing_hint = [s for s in profile_skills if s.lower() not in text]
    return {
        "matching_requirements": matching,
        "partial_matches": [],
        "missing_requirements": [],
        "keywords_found": matching,
        "potential_concerns": [],
        "note": (
            "This is a literal keyword match against your stored skills, not an inferred "
            "assessment. Skills below were not found by name in the job text — that does not "
            "necessarily mean they're irrelevant."
        ),
        "skills_not_mentioned": missing_hint,
    }


async def update_job_status(session: AsyncSession, job_id: str, status: str) -> Job:
    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Valid values: {sorted(VALID_STATUSES)}")
    job = await session.get(Job, job_id)
    if job is None:
        raise ValueError(f"Job {job_id} does not exist.")
    job.status = status
    job.updated_at = datetime.utcnow()
    await session.flush()
    return job
