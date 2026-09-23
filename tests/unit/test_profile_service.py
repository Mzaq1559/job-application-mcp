from __future__ import annotations

import pytest

from job_application_mcp.models.profile import ProfileIn
from job_application_mcp.services import profile_service

pytestmark = pytest.mark.asyncio


async def test_profile_starts_empty(db_session):
    profile = await profile_service.get_profile(db_session)
    assert profile.name is None
    assert profile.skills is None


async def test_profile_update_is_partial(db_session):
    await profile_service.update_profile(db_session, ProfileIn(name="Zulqarnain", skills=["Python", "C++"]))
    updated = await profile_service.update_profile(db_session, ProfileIn(location="Taxila, Pakistan"))

    assert updated.name == "Zulqarnain"  # untouched by the second, partial update
    assert updated.skills == ["Python", "C++"]
    assert updated.location == "Taxila, Pakistan"


async def test_profile_summary_reports_empty_state(db_session):
    summary = await profile_service.profile_summary(db_session)
    assert "empty" in summary.lower()


async def test_profile_summary_uses_only_stored_fields(db_session):
    await profile_service.update_profile(
        db_session, ProfileIn(name="Zulqarnain", skills=["Python", "FastAPI"])
    )
    summary = await profile_service.profile_summary(db_session)
    assert "Zulqarnain" in summary
    assert "Python" in summary
