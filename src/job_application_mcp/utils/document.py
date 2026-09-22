from __future__ import annotations

import os

import pypdf
from docx import Document as DocxDocument


class UnsupportedFileType(ValueError):
    pass


def extract_text(file_path: str) -> str:
    """Best-effort text extraction for pdf / docx / txt / md."""
    ext = os.path.splitext(file_path)[1].lower()

    if ext == ".pdf":
        reader = pypdf.PdfReader(file_path)
        return "\n".join((page.extract_text() or "") for page in reader.pages).strip()

    if ext == ".docx":
        doc = DocxDocument(file_path)
        return "\n".join(p.text for p in doc.paragraphs).strip()

    if ext in (".txt", ".md"):
        with open(file_path, encoding="utf-8", errors="replace") as f:
            return f.read().strip()

    raise UnsupportedFileType(f"Unsupported resume file type: {ext or '(none)'}")


ALLOWED_EXTENSIONS = {".pdf", ".docx", ".txt", ".md"}


def validate_upload(filename: str, size_bytes: int, max_size_mb: int) -> None:
    ext = os.path.splitext(filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UnsupportedFileType(
            f"'{ext}' is not supported. Allowed types: {', '.join(sorted(ALLOWED_EXTENSIONS))}"
        )
    if size_bytes > max_size_mb * 1024 * 1024:
        raise ValueError(f"File exceeds the {max_size_mb}MB upload limit.")
    # Reject path traversal in the provided filename.
    if ".." in filename or filename.startswith("/") or "\\" in filename:
        raise ValueError("Invalid filename.")
