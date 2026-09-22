from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class ApplicationOut(BaseModel):
    id: str
    job_id: str
    status: str
    resume_version_id: str | None = None
    cover_letter: str | None = None
    professional_summary: str | None = None
    submission_method: str | None = None
    submitted_at: datetime | None = None
    notes: str | None = None
