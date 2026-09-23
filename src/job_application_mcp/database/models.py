"""SQLAlchemy ORM models.

Works unchanged against SQLite (dev) or PostgreSQL (prod) — only DATABASE_URL
changes. UUID primary keys stored as strings for portability.
"""

from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Text, func
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def _uuid() -> str:
    return str(uuid.uuid4())


class Base(DeclarativeBase):
    pass


class TimestampMixin:
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Profile(Base, TimestampMixin):
    """A single user's professional profile. One row per deployment (single-user MCP)."""

    __tablename__ = "profiles"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    name: Mapped[str | None] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    # Structured JSON blobs (list-of-dict) for open-ended sections. Kept as
    # Text/JSON rather than fully normalized tables — this is a personal
    # profile, not a multi-tenant system.
    education: Mapped[list | None] = mapped_column("education_json", Text)
    skills: Mapped[list | None] = mapped_column("skills_json", Text)
    projects: Mapped[list | None] = mapped_column("projects_json", Text)
    experience: Mapped[list | None] = mapped_column("experience_json", Text)
    research_interests: Mapped[list | None] = mapped_column("research_interests_json", Text)
    certifications: Mapped[list | None] = mapped_column("certifications_json", Text)
    achievements: Mapped[list | None] = mapped_column("achievements_json", Text)
    preferences: Mapped[dict | None] = mapped_column("preferences_json", Text)

    resumes: Mapped[list[Resume]] = relationship(back_populates="profile", cascade="all, delete-orphan")
    applications: Mapped[list[Application]] = relationship(
        back_populates="profile", cascade="all, delete-orphan"
    )


class Resume(Base, TimestampMixin):
    __tablename__ = "resumes"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    name: Mapped[str] = mapped_column(Text)
    type: Mapped[str | None] = mapped_column(Text)  # e.g. "software-engineering", "ai-ml"
    description: Mapped[str | None] = mapped_column(Text)
    is_active: Mapped[bool] = mapped_column(default=True)

    profile: Mapped[Profile] = relationship(back_populates="resumes")
    versions: Mapped[list[ResumeVersion]] = relationship(
        back_populates="resume", cascade="all, delete-orphan"
    )


class ResumeVersion(Base, TimestampMixin):
    __tablename__ = "resume_versions"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    resume_id: Mapped[str] = mapped_column(ForeignKey("resumes.id"))
    version_number: Mapped[int] = mapped_column(default=1)
    file_path: Mapped[str | None] = mapped_column(Text)
    original_filename: Mapped[str | None] = mapped_column(Text)
    extracted_text: Mapped[str | None] = mapped_column(Text)
    change_notes: Mapped[str | None] = mapped_column(Text)
    is_active_version: Mapped[bool] = mapped_column(default=True)

    resume: Mapped[Resume] = relationship(back_populates="versions")


class Job(Base, TimestampMixin):
    __tablename__ = "jobs"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    title: Mapped[str] = mapped_column(Text)
    company: Mapped[str] = mapped_column(Text)
    location: Mapped[str | None] = mapped_column(Text)
    employment_type: Mapped[str | None] = mapped_column(Text)
    remote_status: Mapped[str | None] = mapped_column(Text)
    source: Mapped[str | None] = mapped_column(Text)  # linkedin, indeed, company-site, ...
    source_url: Mapped[str | None] = mapped_column(Text)
    description: Mapped[str] = mapped_column(Text)  # supplied by the user, never scraped
    requirements: Mapped[str | None] = mapped_column(Text)
    preferred_qualifications: Mapped[str | None] = mapped_column(Text)
    responsibilities: Mapped[str | None] = mapped_column(Text)
    salary: Mapped[str | None] = mapped_column(Text)
    deadline: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(Text, default="saved")
    notes: Mapped[str | None] = mapped_column(Text)
    analysis_json: Mapped[str | None] = mapped_column(Text)  # cached job_analyze() output

    applications: Mapped[list[Application]] = relationship(back_populates="job")


class Application(Base, TimestampMixin):
    __tablename__ = "applications"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    profile_id: Mapped[str] = mapped_column(ForeignKey("profiles.id"))
    job_id: Mapped[str] = mapped_column(ForeignKey("jobs.id"))
    resume_version_id: Mapped[str | None] = mapped_column(ForeignKey("resume_versions.id"))
    status: Mapped[str] = mapped_column(Text, default="saved")
    cover_letter: Mapped[str | None] = mapped_column(Text)
    professional_summary: Mapped[str | None] = mapped_column(Text)
    submission_method: Mapped[str | None] = mapped_column(Text)  # only set to "manual" by user confirmation
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    notes: Mapped[str | None] = mapped_column(Text)

    profile: Mapped[Profile] = relationship(back_populates="applications")
    job: Mapped[Job] = relationship(back_populates="applications")
    documents: Mapped[list[ApplicationDocument]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    screening_questions: Mapped[list[ScreeningQuestion]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    interviews: Mapped[list[Interview]] = relationship(
        back_populates="application", cascade="all, delete-orphan"
    )
    events: Mapped[list[ApplicationEvent]] = relationship(
        back_populates="application", cascade="all, delete-orphan", order_by="ApplicationEvent.created_at"
    )


class ApplicationDocument(Base, TimestampMixin):
    __tablename__ = "application_documents"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    document_type: Mapped[str] = mapped_column(Text)  # resume, cover_letter, portfolio, transcript, ...
    file_path: Mapped[str | None] = mapped_column(Text)
    content: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="documents")


class ScreeningQuestion(Base, TimestampMixin):
    __tablename__ = "screening_questions"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    question: Mapped[str] = mapped_column(Text)
    proposed_answer: Mapped[str | None] = mapped_column(Text)
    evidence: Mapped[str | None] = mapped_column(Text)
    needs_user_input: Mapped[bool] = mapped_column(default=False)
    confirmed_answer: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="screening_questions")


class Interview(Base, TimestampMixin):
    __tablename__ = "interviews"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    scheduled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    timezone: Mapped[str | None] = mapped_column(Text)
    interview_type: Mapped[str | None] = mapped_column(Text)  # phone, technical, onsite, panel, ...
    interviewer: Mapped[str | None] = mapped_column(Text)
    meeting_url: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="interviews")
    notes: Mapped[list[InterviewNote]] = relationship(
        back_populates="interview", cascade="all, delete-orphan"
    )


class InterviewNote(Base, TimestampMixin):
    __tablename__ = "interview_notes"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    interview_id: Mapped[str] = mapped_column(ForeignKey("interviews.id"))
    note_type: Mapped[str] = mapped_column(Text, default="general")  # prep, post-interview, general
    content: Mapped[str] = mapped_column(Text)

    interview: Mapped[Interview] = relationship(back_populates="notes")


class ApplicationEvent(Base, TimestampMixin):
    __tablename__ = "application_events"

    id: Mapped[str] = mapped_column(primary_key=True, default=_uuid)
    application_id: Mapped[str] = mapped_column(ForeignKey("applications.id"))
    event_type: Mapped[str] = mapped_column(Text)
    description: Mapped[str | None] = mapped_column(Text)

    application: Mapped[Application] = relationship(back_populates="events")
