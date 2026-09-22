from __future__ import annotations

import os
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_application_mcp.config.settings import get_settings
from job_application_mcp.database.models import Resume, ResumeVersion
from job_application_mcp.services.profile_service import get_or_create_profile
from job_application_mcp.utils.document import extract_text, validate_upload


async def list_resumes(session: AsyncSession) -> list[Resume]:
    result = await session.execute(select(Resume).order_by(Resume.created_at.desc()))
    return list(result.scalars().all())


async def get_resume(session: AsyncSession, resume_id: str) -> Resume | None:
    return await session.get(Resume, resume_id)


async def create_resume(
    session: AsyncSession,
    *,
    name: str,
    resume_type: str | None,
    description: str | None,
) -> Resume:
    profile = await get_or_create_profile(session)
    resume = Resume(profile_id=profile.id, name=name, type=resume_type, description=description)
    session.add(resume)
    await session.flush()
    return resume


async def upload_resume_version(
    session: AsyncSession,
    *,
    resume_id: str,
    filename: str,
    file_bytes: bytes,
    change_notes: str | None = None,
) -> ResumeVersion:
    """Store a new resume file, extract its text, and mark it the active version.

    The caller (MCP tool layer) is responsible for actually receiving the
    file bytes from the user — this service only validates, persists, and
    extracts text from what it is given.
    """
    settings = get_settings()
    validate_upload(filename, len(file_bytes), settings.max_upload_size_mb)

    resume = await session.get(Resume, resume_id)
    if resume is None:
        raise ValueError(f"Resume {resume_id} does not exist. Call resume_list or create it first.")

    os.makedirs(settings.upload_dir, exist_ok=True)
    ext = os.path.splitext(filename)[1].lower()
    stored_name = f"{uuid.uuid4()}{ext}"
    stored_path = os.path.join(settings.upload_dir, stored_name)
    with open(stored_path, "wb") as f:
        f.write(file_bytes)

    extracted = extract_text(stored_path)

    # Deactivate previous versions, add the new one as active.
    for v in resume.versions:
        v.is_active_version = False
    next_version_number = (max((v.version_number for v in resume.versions), default=0)) + 1

    version = ResumeVersion(
        resume_id=resume.id,
        version_number=next_version_number,
        file_path=stored_path,
        original_filename=filename,
        extracted_text=extracted,
        change_notes=change_notes,
        is_active_version=True,
    )
    session.add(version)
    await session.flush()
    return version


async def delete_resume(session: AsyncSession, resume_id: str) -> bool:
    resume = await session.get(Resume, resume_id)
    if resume is None:
        return False
    for version in resume.versions:
        if version.file_path and os.path.exists(version.file_path):
            os.remove(version.file_path)
    await session.delete(resume)
    await session.flush()
    return True


def _active_text(resume: Resume) -> str:
    for v in resume.versions:
        if v.is_active_version and v.extracted_text:
            return v.extracted_text
    return ""


async def select_resume_for_job(
    session: AsyncSession, *, job_description: str
) -> dict:
    """Simple, transparent keyword-overlap scoring — no fabricated "AI confidence".

    This is a heuristic starting point; job_service / AI-assisted analysis
    tools can layer richer reasoning on top of this later.
    """
    resumes = await list_resumes(session)
    if not resumes:
        return {
            "recommended_resume": None,
            "alternatives": [],
            "matching_skills": [],
            "missing_skills": [],
            "reasoning_summary": "No resumes are stored yet. Use resume_upload first.",
        }

    job_words = {w.lower().strip(".,()") for w in job_description.split() if len(w) > 2}

    scored = []
    for resume in resumes:
        text = _active_text(resume)
        resume_words = {w.lower().strip(".,()") for w in text.split() if len(w) > 2}
        overlap = job_words & resume_words
        scored.append((resume, len(overlap), sorted(overlap)))

    scored.sort(key=lambda t: t[1], reverse=True)
    best, best_score, best_overlap = scored[0]

    return {
        "recommended_resume": {"id": best.id, "name": best.name, "type": best.type},
        "alternatives": [
            {"id": r.id, "name": r.name, "type": r.type, "overlap_score": s}
            for r, s, _ in scored[1:4]
        ],
        "matching_skills": best_overlap[:25],
        "missing_skills": [],  # requires stored profile skills vs. job requirements; left explicit
        "reasoning_summary": (
            f"'{best.name}' shares the most keyword overlap ({best_score} terms) with the job "
            "description among your stored resumes. This is a heuristic match on wording, not a "
            "guarantee of fit — review the job_analyze output for a requirement-by-requirement view."
        ),
    }
