from __future__ import annotations

import base64

from job_application_mcp.database.database import session_scope
from job_application_mcp.mcp_app import mcp
from job_application_mcp.services import resume_service


def _resume_to_dict(resume) -> dict:
    active = next((v for v in resume.versions if v.is_active_version), None)
    return {
        "id": resume.id,
        "name": resume.name,
        "type": resume.type,
        "description": resume.description,
        "is_active": resume.is_active,
        "created_at": resume.created_at.isoformat() if resume.created_at else None,
        "updated_at": resume.updated_at.isoformat() if resume.updated_at else None,
        "active_version": (
            {
                "id": active.id,
                "version_number": active.version_number,
                "original_filename": active.original_filename,
            }
            if active
            else None
        ),
        "version_count": len(resume.versions),
    }


@mcp.tool()
async def resume_list() -> list[dict]:
    """List all stored resumes with their id, name, type, description, and
    active-version info. Use the returned id with resume_get, resume_update,
    resume_delete, or as an input to resume_select_for_job."""
    async with session_scope() as session:
        resumes = await resume_service.list_resumes(session)
        return [_resume_to_dict(r) for r in resumes]


@mcp.tool()
async def resume_get(resume_id: str) -> dict:
    """Retrieve a resume's metadata plus the extracted text of its active
    version, so the content can be used for analysis or cover-letter writing."""
    async with session_scope() as session:
        resume = await resume_service.get_resume(session, resume_id)
        if resume is None:
            raise ValueError(f"No resume found with id {resume_id}.")
        data = _resume_to_dict(resume)
        active = next((v for v in resume.versions if v.is_active_version), None)
        data["extracted_text"] = active.extracted_text if active else None
        return data


@mcp.tool()
async def resume_upload(
    filename: str,
    content_base64: str,
    resume_id: str | None = None,
    name: str | None = None,
    resume_type: str | None = None,
    description: str | None = None,
    change_notes: str | None = None,
) -> dict:
    """Add a resume file. `content_base64` is the file's bytes, base64-encoded
    (pdf, docx, txt, or md). If `resume_id` is given, this becomes a new
    version of that existing resume; otherwise a new resume record is created
    using `name`/`resume_type`/`description` (name is required in that case).
    Text is extracted automatically. Max size is configured server-side."""
    file_bytes = base64.b64decode(content_base64)

    async with session_scope() as session:
        if resume_id is None:
            if not name:
                raise ValueError("`name` is required when creating a new resume (resume_id not given).")
            resume = await resume_service.create_resume(
                session, name=name, resume_type=resume_type, description=description
            )
            resume_id = resume.id

        version = await resume_service.upload_resume_version(
            session,
            resume_id=resume_id,
            filename=filename,
            file_bytes=file_bytes,
            change_notes=change_notes,
        )
        return {
            "resume_id": resume_id,
            "version_id": version.id,
            "version_number": version.version_number,
            "original_filename": version.original_filename,
            "extracted_characters": len(version.extracted_text or ""),
        }


@mcp.tool()
async def resume_update(resume_id: str, name: str | None = None, resume_type: str | None = None, description: str | None = None, is_active: bool | None = None) -> dict:
    """Update a resume's metadata (not its file content — use resume_upload for a new version)."""
    async with session_scope() as session:
        resume = await resume_service.get_resume(session, resume_id)
        if resume is None:
            raise ValueError(f"No resume found with id {resume_id}.")
        if name is not None:
            resume.name = name
        if resume_type is not None:
            resume.type = resume_type
        if description is not None:
            resume.description = description
        if is_active is not None:
            resume.is_active = is_active
        await session.flush()
        return _resume_to_dict(resume)


@mcp.tool()
async def resume_delete(resume_id: str, confirm: bool = False) -> str:
    """Permanently delete a resume and all its versions/files. Destructive —
    requires confirm=true, and should only be called after the user has
    explicitly confirmed they want it deleted."""
    if not confirm:
        return "Not deleted: pass confirm=true after the user explicitly confirms deletion."
    async with session_scope() as session:
        deleted = await resume_service.delete_resume(session, resume_id)
        return "Resume deleted." if deleted else f"No resume found with id {resume_id}."


@mcp.tool()
async def resume_select_for_job(job_description: str) -> dict:
    """Given a job description, recommend which stored resume is the best
    fit using transparent keyword overlap (not a fabricated confidence score).
    Returns the recommended resume, ranked alternatives, and the reasoning."""
    async with session_scope() as session:
        return await resume_service.select_resume_for_job(session, job_description=job_description)
