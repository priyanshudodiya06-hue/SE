from __future__ import annotations

from typing import Optional

import PyPDF2

from ai_client import get_resume_feedback


def extract_resume_text(uploaded_file) -> str:
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return _extract_pdf_text(uploaded_file)

    if file_name.endswith(".txt"):
        return uploaded_file.getvalue().decode("utf-8", errors="ignore").strip()

    raise ValueError("Unsupported file type. Please upload a PDF or TXT file.")


def _extract_pdf_text(uploaded_file) -> str:
    reader = PyPDF2.PdfReader(uploaded_file)
    pages = []

    for page in reader.pages:
        page_text = page.extract_text() or ""
        if page_text.strip():
            pages.append(page_text.strip())

    return "\n\n".join(pages).strip()


def analyze_resume(
    text: str,
    target_role: Optional[str] = None,
    provider: str = "local",
    model: Optional[str] = None,
) -> str:
    clean_text = text.strip()
    if not clean_text:
        raise ValueError("The uploaded resume is empty or unreadable.")

    return get_resume_feedback(
        clean_text,
        target_role=target_role,
        provider=provider,
        model=model,
    )
