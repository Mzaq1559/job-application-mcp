from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from job_application_mcp.database.models import Application, ApplicationEvent
from job_application_mcp.services.profile_service import get_or_create_profile

VALID_TRANSITIONS: dict[str, set[str]] = {
    "saved": {"analyzing", "ready_to_apply", "withdrawn"},
    "analyzing": {"ready_to_apply", "saved", "withdrawn"},
    "ready_to_apply": {"applied", "withdrawn"},
    "applied": {"screening", "rejected", "withdrawn"},
    "screening": {"interview", "rejected", "withdrawn"},
    "interview": {"offer", "rejected", "withdrawn"},
    "offer": {"rejected", "withdrawn"},
    "rejected": set(),
    "withdrawn": set(),
}


async def _log_event(
    session: AsyncSession,
    application_id: str,
    event_type: str,
    description: str | None = None,
) -> None:
    session.add(
        ApplicationEvent(application_id=application_id, event_type=event_type, description=description)
    )


async def create_application(
    session: AsyncSession, *, job_id: str, resume_version_id: str | None = None
) -> Application:
    profile = await get_or_create_profile(session)

    existing = await session.execute(
        select(Application).where(Application.job_id == job_id, Application.profile_id == profile.id)
    )
    if existing.scalars().first() is not None:
        raise ValueError(
            "DUPLICATE APPLICATION DETECTED: an application for this job already exists. "
            "Use application_get to view it instead of creating a new one."
        )

    application = Application(profile_id=profile.id, job_id=job_id, resume_version_id=resume_version_id)
    session.add(application)
    await session.flush()
    await _log_event(session, application.id, "created", "Application record created.")
    await session.flush()
    return application


async def get_application(session: AsyncSession, application_id: str) -> Application | None:
    result = await session.execute(
        select(Application)
        .options(selectinload(Application.events), selectinload(Application.screening_questions))
        .where(Application.id == application_id)
    )
    return result.scalar_one_or_none()


async def list_applications(session: AsyncSession, *, status: str | None = None) -> list[Application]:
    stmt = select(Application)
    if status:
        stmt = stmt.where(Application.status == status)
    result = await session.execute(stmt.order_by(Application.created_at.desc()))
    return list(result.scalars().all())


async def update_application_status(
    session: AsyncSession, application_id: str, new_status: str
) -> Application:
    application = await session.get(Application, application_id)
    if application is None:
        raise ValueError(f"Application {application_id} does not exist.")

    allowed = VALID_TRANSITIONS.get(application.status, set())
    if new_status not in allowed and new_status != application.status:
        raise ValueError(
            f"Cannot move application from '{application.status}' to '{new_status}'. "
            f"Valid next states: {sorted(allowed) or '(none — terminal status)'}"
        )

    old_status = application.status
    application.status = new_status
    if new_status == "applied":
        # Only ever set by an explicit user confirmation — see application tools layer.
        application.submission_method = "manual"
        application.submitted_at = datetime.now(UTC)

    await session.flush()
    await _log_event(session, application.id, "status_changed", f"{old_status} -> {new_status}")
    await session.flush()
    return application


async def application_history(session: AsyncSession, application_id: str) -> list[ApplicationEvent]:
    result = await session.execute(
        select(ApplicationEvent)
        .where(ApplicationEvent.application_id == application_id)
        .order_by(ApplicationEvent.created_at)
    )
    return list(result.scalars().all())


async def delete_application(session: AsyncSession, application_id: str) -> bool:
    application = await session.get(Application, application_id)
    if application is None:
        return False
    await session.delete(application)
    await session.flush()
    return True
