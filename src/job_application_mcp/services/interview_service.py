from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from job_application_mcp.database.models import Interview, InterviewNote


async def create_interview(session: AsyncSession, *, application_id: str, **fields) -> Interview:
    interview = Interview(application_id=application_id, **fields)
    session.add(interview)
    await session.flush()
    return interview


async def list_interviews(session: AsyncSession, *, application_id: str | None = None) -> list[Interview]:
    stmt = select(Interview)
    if application_id:
        stmt = stmt.where(Interview.application_id == application_id)
    result = await session.execute(stmt.order_by(Interview.scheduled_at))
    return list(result.scalars().all())


async def add_interview_note(
    session: AsyncSession, *, interview_id: str, note_type: str, content: str
) -> InterviewNote:
    note = InterviewNote(interview_id=interview_id, note_type=note_type, content=content)
    session.add(note)
    await session.flush()
    return note


async def update_interview(session: AsyncSession, interview_id: str, **fields) -> Interview:
    interview = await session.get(Interview, interview_id)
    if interview is None:
        raise ValueError(f"Interview {interview_id} does not exist.")
    for key, value in fields.items():
        if value is not None and hasattr(interview, key):
            setattr(interview, key, value)
    await session.flush()
    return interview
