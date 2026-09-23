from __future__ import annotations

import pytest

from job_application_mcp.models.job import JobIn
from job_application_mcp.services import application_service, job_service

pytestmark = pytest.mark.asyncio


async def _make_job(session):
    return await job_service.create_job(
        session,
        JobIn(title="Backend Intern", company="Example Co", description="Build APIs with FastAPI."),
    )


async def test_create_application(db_session):
    job = await _make_job(db_session)
    app = await application_service.create_application(db_session, job_id=job.id)
    assert app.status == "saved"


async def test_duplicate_application_rejected(db_session):
    job = await _make_job(db_session)
    await application_service.create_application(db_session, job_id=job.id)
    with pytest.raises(ValueError, match="DUPLICATE"):
        await application_service.create_application(db_session, job_id=job.id)


async def test_valid_status_transition(db_session):
    job = await _make_job(db_session)
    app = await application_service.create_application(db_session, job_id=job.id)
    updated = await application_service.update_application_status(db_session, app.id, "analyzing")
    assert updated.status == "analyzing"


async def test_invalid_status_transition_rejected(db_session):
    job = await _make_job(db_session)
    app = await application_service.create_application(db_session, job_id=job.id)
    # saved -> interview is not a legal direct transition
    with pytest.raises(ValueError):
        await application_service.update_application_status(db_session, app.id, "interview")


async def test_marking_applied_records_manual_submission(db_session):
    job = await _make_job(db_session)
    app = await application_service.create_application(db_session, job_id=job.id)
    await application_service.update_application_status(db_session, app.id, "ready_to_apply")
    applied = await application_service.update_application_status(db_session, app.id, "applied")
    assert applied.submission_method == "manual"
    assert applied.submitted_at is not None


async def test_history_records_events(db_session):
    job = await _make_job(db_session)
    app = await application_service.create_application(db_session, job_id=job.id)
    await application_service.update_application_status(db_session, app.id, "analyzing")
    events = await application_service.application_history(db_session, app.id)
    event_types = [e.event_type for e in events]
    assert "created" in event_types
    assert "status_changed" in event_types
