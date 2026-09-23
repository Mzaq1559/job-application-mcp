from __future__ import annotations

import pytest

from job_application_mcp.models.job import JobIn
from job_application_mcp.services import job_service

pytestmark = pytest.mark.asyncio


def _job_in(**overrides) -> JobIn:
    defaults = dict(
        title="AI Research Intern",
        company="Example AI",
        description="Work on computer vision pipelines using Python and PyTorch.",
        source_url="https://example.com/jobs/123",
    )
    defaults.update(overrides)
    return JobIn(**defaults)


async def test_create_and_get_job(db_session):
    job = await job_service.create_job(db_session, _job_in())
    fetched = await job_service.get_job(db_session, job.id)
    assert fetched is not None
    assert fetched.title == "AI Research Intern"
    assert fetched.status == "saved"


async def test_duplicate_detection_by_url(db_session):
    await job_service.create_job(db_session, _job_in())
    duplicate = await job_service.find_possible_duplicate(db_session, _job_in(title="Different Title"))
    assert duplicate is not None


async def test_duplicate_detection_by_company_and_title(db_session):
    await job_service.create_job(db_session, _job_in(source_url=None))
    duplicate = await job_service.find_possible_duplicate(
        db_session, _job_in(source_url=None, description="different text")
    )
    assert duplicate is not None


async def test_no_duplicate_for_distinct_job(db_session):
    await job_service.create_job(db_session, _job_in())
    duplicate = await job_service.find_possible_duplicate(
        db_session, _job_in(title="Backend Intern", company="Other Co", source_url="https://example.com/999")
    )
    assert duplicate is None


async def test_analyze_job_only_reports_literal_matches():
    analysis = job_service.analyze_job(
        job_description="We need someone skilled in Python and React.",
        requirements="3+ years experience",
        profile_skills=["Python", "React", "Rust"],
    )
    assert "Python" in analysis["matching_requirements"]
    assert "React" in analysis["matching_requirements"]
    assert "Rust" in analysis["skills_not_mentioned"]


async def test_update_job_status_rejects_invalid_status(db_session):
    job = await job_service.create_job(db_session, _job_in())
    with pytest.raises(ValueError):
        await job_service.update_job_status(db_session, job.id, "not_a_real_status")
