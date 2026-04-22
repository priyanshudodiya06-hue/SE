from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Optional


SECTION_KEYWORDS = {
    "education": ["education", "academic", "university", "college", "school"],
    "skills": ["skills", "technical skills", "tools", "technologies", "stack"],
    "experience": ["experience", "work experience", "internship", "employment"],
    "projects": ["projects", "project"],
    "contact": ["email", "phone", "linkedin", "github"],
}

ACTION_VERBS = {
    "built",
    "created",
    "developed",
    "designed",
    "implemented",
    "improved",
    "managed",
    "optimized",
    "led",
    "delivered",
    "analyzed",
    "collaborated",
    "automated",
}

TECH_KEYWORDS = {
    "python",
    "java",
    "c++",
    "c",
    "javascript",
    "typescript",
    "html",
    "css",
    "sql",
    "streamlit",
    "django",
    "flask",
    "react",
    "node",
    "git",
    "github",
    "aws",
    "azure",
    "docker",
    "machine learning",
    "data analysis",
}

DEFAULT_OPENAI_MODEL = "gpt-4o-mini"
DEFAULT_GEMINI_MODEL = "gemini-1.5-flash"


def _load_local_env() -> None:
    env_path = Path(__file__).resolve().parent / ".env"
    if not env_path.exists():
        return

    for raw_line in env_path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue

        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


_load_local_env()


def _normalize_text(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _line_split(text: str) -> list[str]:
    return [line.strip() for line in text.splitlines() if line.strip()]


def _count_matches(text: str, words: set[str]) -> int:
    lowered = text.lower()
    return sum(1 for word in words if word in lowered)


def _has_section(text: str, keywords: list[str]) -> bool:
    lowered = text.lower()
    return any(keyword in lowered for keyword in keywords)


def _score_resume(resume_text: str, target_role: Optional[str]) -> tuple[int, list[str], list[str], list[str]]:
    strengths: list[str] = []
    weaknesses: list[str] = []
    suggestions: list[str] = []
    score = 0

    normalized = _normalize_text(resume_text)
    lines = _line_split(resume_text)
    lowered = normalized.lower()

    word_count = len(normalized.split())
    number_hits = len(re.findall(r"\d+%?|\b\d+(?:\.\d+)?\b", resume_text))
    verb_hits = _count_matches(lowered, ACTION_VERBS)
    tech_hits = _count_matches(lowered, TECH_KEYWORDS)

    present_sections = {
        name: _has_section(resume_text, keywords)
        for name, keywords in SECTION_KEYWORDS.items()
    }

    if word_count >= 180:
        strengths.append("The resume has enough written content to evaluate your background.")
        score += 1
    else:
        weaknesses.append("The resume looks very short and may not show enough detail about your work.")
        suggestions.append("Add more detail about projects, internships, coursework, or achievements.")

    if present_sections["contact"]:
        strengths.append("Basic contact information appears to be present.")
        score += 1
    else:
        weaknesses.append("Contact details are missing or not clearly visible.")
        suggestions.append("Include email, phone number, and links like LinkedIn or GitHub.")

    if present_sections["education"]:
        strengths.append("Education details are included.")
        score += 1
    else:
        weaknesses.append("Education information is missing or unclear.")
        suggestions.append("Add your degree, college, graduation year, and relevant academic details.")

    if present_sections["skills"]:
        strengths.append("A skills section is present.")
        score += 1
    else:
        weaknesses.append("There is no clear skills section.")
        suggestions.append("Add a separate skills section for languages, tools, and frameworks.")

    if present_sections["experience"] or present_sections["projects"]:
        strengths.append("The resume includes practical work such as projects or experience.")
        score += 1
    else:
        weaknesses.append("Projects or experience are not clearly shown.")
        suggestions.append("Add project work or internship experience to demonstrate hands-on ability.")

    if number_hits >= 3:
        strengths.append("The resume uses measurable results or numbers, which makes impact stronger.")
        score += 1
    else:
        weaknesses.append("There are very few measurable achievements or numbers.")
        suggestions.append("Use numbers where possible, such as percentages, users, time saved, or marks.")

    if verb_hits >= 3:
        strengths.append("Action-oriented language makes the resume sound more professional.")
        score += 1
    else:
        weaknesses.append("Bullet points could use stronger action verbs.")
        suggestions.append("Start experience and project points with action verbs like built, developed, or led.")

    if tech_hits >= 4:
        strengths.append("Relevant technical keywords improve clarity about your skills.")
        score += 1
    else:
        weaknesses.append("Technical skills are not described strongly enough.")
        suggestions.append("Mention the main technologies you used in projects and coursework.")

    if target_role:
        role_words = [word for word in re.findall(r"[a-zA-Z]+", target_role.lower()) if len(word) > 2]
        role_matches = sum(1 for word in role_words if word in lowered)
        if role_matches >= max(1, len(role_words) // 2):
            strengths.append(f"The resume appears somewhat aligned with the target role: {target_role}.")
            score += 1
        else:
            weaknesses.append(f"The resume is not clearly tailored to the target role: {target_role}.")
            suggestions.append(
                f"Customize your summary, skills, and project descriptions for the role '{target_role}'."
            )

    if len(lines) >= 8:
        score += 1
        strengths.append("The resume has a structured amount of content across multiple lines.")
    else:
        weaknesses.append("The formatting may be too limited or compressed.")
        suggestions.append("Use clear section headings and separate entries with bullet points or spacing.")

    score = max(1, min(score, 10))

    if not suggestions:
        suggestions.append("Polish wording and tailor the resume slightly for each job application.")

    return score, strengths[:4], weaknesses[:4], suggestions[:4]


def _format_local_feedback(resume_text: str, target_role: Optional[str] = None) -> str:
    score, strengths, weaknesses, suggestions = _score_resume(resume_text, target_role)

    strengths_md = "\n".join(f"- {item}" for item in strengths) or "- No clear strengths detected."
    weaknesses_md = "\n".join(f"- {item}" for item in weaknesses) or "- No major weaknesses detected."
    suggestions_md = "\n".join(f"- {item}" for item in suggestions)

    return (
        "## Strengths\n"
        f"{strengths_md}\n\n"
        "## Weaknesses\n"
        f"{weaknesses_md}\n\n"
        "## Suggestions for Improvement\n"
        f"{suggestions_md}\n\n"
        "## Score\n"
        f"**{score}/10**"
    )


def _build_prompt(resume_text: str, target_role: Optional[str]) -> str:
    role_line = target_role if target_role else "No specific target role provided."
    return (
        "Analyze the resume below and return Markdown with exactly these sections:\n"
        "## Strengths\n"
        "- bullet points only\n\n"
        "## Weaknesses\n"
        "- bullet points only\n\n"
        "## Suggestions for Improvement\n"
        "- bullet points only\n\n"
        "## Score\n"
        "**X/10**\n\n"
        "Keep the feedback practical and concise. Focus on resume quality, relevance, structure, and impact.\n"
        f"Target role: {role_line}\n\n"
        "Resume text:\n"
        f"{resume_text}"
    )


def _read_api_key(provider: str) -> Optional[str]:
    provider = provider.lower()
    if provider == "openai":
        return os.getenv("OPENAI_API_KEY") or os.getenv("OPENAI_KEY")
    if provider == "gemini":
        return os.getenv("GEMINI_API_KEY") or os.getenv("GOOGLE_API_KEY")
    return None


def _http_post_json(url: str, payload: dict, headers: dict[str, str]) -> dict:
    data = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(url, data=data, headers=headers, method="POST")
    with urllib.request.urlopen(request, timeout=60) as response:
        response_body = response.read().decode("utf-8")
    return json.loads(response_body)


def _openai_feedback(resume_text: str, target_role: Optional[str], model: str) -> str:
    api_key = _read_api_key("openai")
    if not api_key:
        raise ValueError("OPENAI_API_KEY is not set.")

    payload = {
        "model": model or DEFAULT_OPENAI_MODEL,
        "messages": [
            {
                "role": "system",
                "content": "You are an expert resume reviewer. Always return feedback in Markdown format with exactly these sections: ## Strengths, ## Weaknesses, ## Suggestions for Improvement, and ## Score as **X/10**."
            },
            {
                "role": "user",
                "content": _build_prompt(resume_text, target_role)
            }
        ],
        "temperature": 0.7,
        "max_tokens": 1500
    }

    response = _http_post_json(
        "https://api.openai.com/v1/chat/completions",
        payload,
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
    )
    
    choices = response.get("choices", [])
    if not choices:
        raise ValueError("OpenAI returned an empty response.")
    
    message = choices[0].get("message", {})
    text = message.get("content", "").strip()
    if text:
        return text

    raise ValueError("OpenAI returned empty message content.")


def _gemini_feedback(resume_text: str, target_role: Optional[str], model: str) -> str:
    api_key = _read_api_key("gemini")
    if not api_key:
        raise ValueError("GEMINI_API_KEY is not set.")

    payload = {
        "contents": [
            {
                "parts": [
                    {
                        "text": _build_prompt(resume_text, target_role),
                    }
                ]
            }
        ],
        "generationConfig": {
            "temperature": 0.3,
        },
    }

    response = _http_post_json(
        f"https://generativelanguage.googleapis.com/v1beta/models/{model or DEFAULT_GEMINI_MODEL}:generateContent?key={api_key}",
        payload,
        {
            "Content-Type": "application/json",
        },
    )
    candidates = response.get("candidates", [])
    if not candidates:
        raise ValueError("Gemini did not return any candidates.")

    parts = candidates[0].get("content", {}).get("parts", [])
    text = "".join(part.get("text", "") for part in parts).strip()
    if not text:
        raise ValueError("Gemini returned an empty response.")
    return text


def get_resume_feedback(
    resume_text: str,
    target_role: Optional[str] = None,
    provider: str = "local",
    model: Optional[str] = None,
) -> str:
    selected_provider = (provider or "local").lower()

    if selected_provider == "local":
        return _format_local_feedback(resume_text, target_role)

    try:
        if selected_provider == "openai":
            return _openai_feedback(resume_text, target_role, model or DEFAULT_OPENAI_MODEL)
        if selected_provider == "gemini":
            return _gemini_feedback(resume_text, target_role, model or DEFAULT_GEMINI_MODEL)
        raise ValueError(f"Unsupported provider: {provider}")
    except urllib.error.HTTPError as exc:
        details = exc.read().decode("utf-8", errors="ignore")
        raise ValueError(f"{selected_provider.title()} API request failed: {details or exc.reason}") from exc
    except urllib.error.URLError as exc:
        raise ValueError(f"Could not reach the {selected_provider.title()} API: {exc.reason}") from exc
