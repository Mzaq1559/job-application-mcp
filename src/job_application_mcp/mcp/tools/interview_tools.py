from __future__ import annotations

from job_application_mcp.database.database import session_scope
from job_application_mcp.mcp_app import mcp
from job_application_mcp.services import interview_service


def _interview_to_dict(iv) -> dict:
    return {
        "id": iv.id,
        "application_id": iv.application_id,
        "scheduled_at": iv.scheduled_at.isoformat() if iv.scheduled_at else None,
        "timezone": iv.timezone,
        "interview_type": iv.interview_type,
        "interviewer": iv.interviewer,
        "meeting_url": iv.meeting_url,
    }


@mcp.tool()
async def interview_create(
    application_id: str,
    scheduled_at: str | None = None,
    timezone: str | None = None,
    interview_type: str | None = None,
    interviewer: str | None = None,
    meeting_url: str | None = None,
) -> dict:
    """Record an interview for a tracked application. `scheduled_at` is an ISO
    8601 datetime string if known."""
    from datetime import datetime as _dt

    async with session_scope() as session:
        iv = await interview_service.create_interview(
            session,
            application_id=application_id,
            scheduled_at=_dt.fromisoformat(scheduled_at) if scheduled_at else None,
            timezone=timezone,
            interview_type=interview_type,
            interviewer=interviewer,
            meeting_url=meeting_url,
        )
        return _interview_to_dict(iv)


@mcp.tool()
async def interview_list(application_id: str | None = None) -> list[dict]:
    """List recorded interviews, optionally scoped to one application."""
    async with session_scope() as session:
        interviews = await interview_service.list_interviews(session, application_id=application_id)
        return [_interview_to_dict(iv) for iv in interviews]


@mcp.tool()
async def interview_update(
    interview_id: str,
    scheduled_at: str | None = None,
    timezone: str | None = None,
    interview_type: str | None = None,
    interviewer: str | None = None,
    meeting_url: str | None = None,
) -> dict:
    """Update details of a recorded interview. Only passed fields are changed."""
    from datetime import datetime as _dt

    async with session_scope() as session:
        iv = await interview_service.update_interview(
            session,
            interview_id,
            scheduled_at=_dt.fromisoformat(scheduled_at) if scheduled_at else None,
            timezone=timezone,
            interview_type=interview_type,
            interviewer=interviewer,
            meeting_url=meeting_url,
        )
        return _interview_to_dict(iv)


@mcp.tool()
async def interview_notes(interview_id: str, note_type: str, content: str) -> dict:
    """Attach a preparation or post-interview note to a recorded interview.
    `note_type` is typically 'prep', 'post-interview', or 'general'."""
    async with session_scope() as session:
        note = await interview_service.add_interview_note(
            session, interview_id=interview_id, note_type=note_type, content=content
        )
        return {"id": note.id, "note_type": note.note_type, "content": note.content}
