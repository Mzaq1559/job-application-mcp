from __future__ import annotations

from datetime import datetime

from job_application_mcp.database.database import session_scope
from job_application_mcp.mcp_app import mcp
from job_application_mcp.models.job import JobIn
from job_application_mcp.services import job_service, profile_service


def _job_to_dict(job) -> dict:
    return {
        "id": job.id,
        "title": job.title,
        "company": job.company,
        "location": job.location,
        "employment_type": job.employment_type,
        "remote_status": job.remote_status,
        "source": job.source,
        "source_url": job.source_url,
        "status": job.status,
        "deadline": job.deadline.isoformat() if job.deadline else None,
        "created_at": job.created_at.isoformat() if job.created_at else None,
    }


@mcp.tool()
async def job_create(
    title: str,
    company: str,
    description: str,
    location: str | None = None,
    employment_type: str | None = None,
    remote_status: str | None = None,
    source: str | None = None,
    source_url: str | None = None,
    requirements: str | None = None,
    preferred_qualifications: str | None = None,
    responsibilities: str | None = None,
    salary: str | None = None,
    deadline: str | None = None,
) -> dict:
    """Save a job the user found. `description` must be text the user supplied
    (pasted from a listing or typed) — this tool never fetches or scrapes a
    URL itself. Checks for a likely duplicate first (same source_url, or same
    company+title) and returns that instead of creating a new record."""
    payload = JobIn(
        title=title,
        company=company,
        description=description,
        location=location,
        employment_type=employment_type,
        remote_status=remote_status,
        source=source,
        source_url=source_url,
        requirements=requirements,
        preferred_qualifications=preferred_qualifications,
        responsibilities=responsibilities,
        salary=salary,
        deadline=datetime.fromisoformat(deadline) if deadline else None,
    )
    async with session_scope() as session:
        duplicate = await job_service.find_possible_duplicate(session, payload)
        if duplicate:
            return {"duplicate": True, "existing_job": _job_to_dict(duplicate)}
        job = await job_service.create_job(session, payload)
        return {"duplicate": False, "job": _job_to_dict(job)}


@mcp.tool()
async def job_get(job_id: str) -> dict:
    """Retrieve full details for a saved job, including its stored description
    and requirements text."""
    async with session_scope() as session:
        job = await job_service.get_job(session, job_id)
        if job is None:
            raise ValueError(f"No job found with id {job_id}.")
        data = _job_to_dict(job)
        data.update(
            description=job.description,
            requirements=job.requirements,
            preferred_qualifications=job.preferred_qualifications,
            responsibilities=job.responsibilities,
            salary=job.salary,
            notes=job.notes,
        )
        return data


@mcp.tool()
async def job_list(status: str | None = None, company: str | None = None) -> list[dict]:
    """List saved jobs, optionally filtered by status or company (substring match)."""
    async with session_scope() as session:
        jobs = await job_service.list_jobs(session, status=status, company=company)
        return [_job_to_dict(j) for j in jobs]


@mcp.tool()
async def job_analyze(job_id: str) -> dict:
    """Compare a saved job's description/requirements against the user's
    stored profile skills. Returns a transparent, literal keyword comparison
    — not a fabricated hireability score. Missing/unclear items are reported
    as such rather than guessed."""
    async with session_scope() as session:
        job = await job_service.get_job(session, job_id)
        if job is None:
            raise ValueError(f"No job found with id {job_id}.")
        profile = await profile_service.get_profile(session)
        analysis = job_service.analyze_job(job.description, job.requirements, profile.skills or [])
        job.analysis_json = None  # placeholder for future cached-analysis storage
        return analysis


@mcp.tool()
async def job_update_status(job_id: str, status: str) -> dict:
    """Update a saved job's status (saved, analyzing, ready_to_apply, applied,
    screening, interview, offer, rejected, withdrawn, closed)."""
    async with session_scope() as session:
        job = await job_service.update_job_status(session, job_id, status)
        return _job_to_dict(job)
