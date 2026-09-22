from __future__ import annotations

from job_application_mcp.database.database import session_scope
from job_application_mcp.mcp_app import mcp
from job_application_mcp.services import application_service


def _application_to_dict(app) -> dict:
    return {
        "id": app.id,
        "job_id": app.job_id,
        "status": app.status,
        "resume_version_id": app.resume_version_id,
        "submission_method": app.submission_method,
        "submitted_at": app.submitted_at.isoformat() if app.submitted_at else None,
        "notes": app.notes,
    }


@mcp.tool()
async def application_create(job_id: str, resume_version_id: str | None = None) -> dict:
    """Create a persistent application record for a saved job. Do not call this
    until the user has actually decided to track this application — it is not
    a submission, just the start of a tracked record. Rejects duplicates: if
    an application already exists for this job, an error is returned instead."""
    async with session_scope() as session:
        app = await application_service.create_application(
            session, job_id=job_id, resume_version_id=resume_version_id
        )
        return _application_to_dict(app)


@mcp.tool()
async def application_get(application_id: str) -> dict:
    """Retrieve full details of one application, including its cover letter,
    screening question answers, and status."""
    async with session_scope() as session:
        app = await application_service.get_application(session, application_id)
        if app is None:
            raise ValueError(f"No application found with id {application_id}.")
        data = _application_to_dict(app)
        data["cover_letter"] = app.cover_letter
        data["professional_summary"] = app.professional_summary
        data["screening_questions"] = [
            {
                "id": q.id,
                "question": q.question,
                "proposed_answer": q.proposed_answer,
                "needs_user_input": q.needs_user_input,
                "confirmed_answer": q.confirmed_answer,
            }
            for q in app.screening_questions
        ]
        return data


@mcp.tool()
async def application_list(status: str | None = None) -> list[dict]:
    """List tracked applications, optionally filtered by status."""
    async with session_scope() as session:
        apps = await application_service.list_applications(session, status=status)
        return [_application_to_dict(a) for a in apps]


@mcp.tool()
async def application_update_status(application_id: str, status: str) -> dict:
    """Move an application to a new status, following the allowed workflow
    (saved -> analyzing -> ready_to_apply -> applied -> screening -> interview
    -> offer, with rejected/withdrawn reachable from most states). Setting
    status to 'applied' should only happen after the user has told you they
    personally submitted the application — this tool never submits anything
    itself; it only records what the user reports."""
    async with session_scope() as session:
        app = await application_service.update_application_status(session, application_id, status)
        return _application_to_dict(app)


@mcp.tool()
async def application_history(application_id: str) -> list[dict]:
    """Return the chronological event history for an application (created,
    status changes, etc.)."""
    async with session_scope() as session:
        events = await application_service.application_history(session, application_id)
        return [
            {"event_type": e.event_type, "description": e.description, "at": e.created_at.isoformat()}
            for e in events
        ]


@mcp.tool()
async def application_delete(application_id: str, confirm: bool = False) -> str:
    """Permanently delete an application record and its associated documents,
    screening answers, interviews, and history. Requires confirm=true after
    the user has explicitly confirmed."""
    if not confirm:
        return "Not deleted: pass confirm=true after the user explicitly confirms deletion."
    async with session_scope() as session:
        deleted = await application_service.delete_application(session, application_id)
        return "Application deleted." if deleted else f"No application found with id {application_id}."
