from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel


class JobIn(BaseModel):
    title: str
    company: str
    description: str
    location: str | None = None
    employment_type: str | None = None
    remote_status: str | None = None
    source: str | None = None
    source_url: str | None = None
    requirements: str | None = None
    preferred_qualifications: str | None = None
    responsibilities: str | None = None
    salary: str | None = None
    deadline: datetime | None = None


class JobOut(JobIn):
    id: str
    status: str
