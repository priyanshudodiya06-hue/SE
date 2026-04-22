import re

import streamlit as st

from analyzer import analyze_resume, extract_resume_text


def extract_score(result_text: str) -> str | None:
    match = re.search(r"\*\*(\d+/10)\*\*", result_text)
    return match.group(1) if match else None


def extract_section(result_text: str, heading: str) -> list[str]:
    pattern = rf"## {re.escape(heading)}\n(.*?)(?=\n## |\Z)"
    match = re.search(pattern, result_text, re.S)
    if not match:
        return []

    items = []
    for line in match.group(1).splitlines():
        line = line.strip()
        if line.startswith("- "):
            items.append(line[2:])
    return items


def render_card(title: str, items: list[str], tone: str) -> None:
    bullet_items = "".join(f"<li>{item}</li>" for item in items) or "<li>No details available.</li>"
    st.markdown(
        f"""
        <div class="content-card {tone}">
            <div class="card-heading">{title}</div>
            <ul class="card-list">{bullet_items}</ul>
        </div>
        """,
        unsafe_allow_html=True,
    )


st.set_page_config(page_title="Smart Resume Analyzer", layout="wide")

st.markdown(
    """
    <style>
    :root {
        --bg: #f7f4ee;
        --surface: #fffdf8;
        --surface-soft: #f2ede3;
        --border: #d8cfc1;
        --text: #1f2a24;
        --muted: #53645b;
        --green: #1f5c4d;
        --green-soft: #dff0ea;
        --amber-soft: #fff0d3;
        --blue-soft: #e8f2f8;
    }

    html, body, .stApp, [class*="css"] {
        color: var(--text);
        font-family: "Trebuchet MS", "Segoe UI", sans-serif;
    }

    .stApp {
        background:
            radial-gradient(circle at 0% 0%, rgba(255, 182, 193, 0.24), transparent 30%),
            radial-gradient(circle at 100% 0%, rgba(173, 216, 230, 0.22), transparent 30%),
            radial-gradient(circle at 50% 100%, rgba(221, 160, 221, 0.18), transparent 34%),
            linear-gradient(180deg, #fff7fb 0%, #eef6ff 100%);
    }

    .block-container {
        max-width: 1140px;
        padding-top: 2rem;
        padding-bottom: 2rem;
    }

    h1, h2, h3, h4, h5, h6, p, label, span {
        color: var(--text) !important;
    }

    [data-testid="stMarkdownContainer"] p,
    [data-testid="stCaptionContainer"] {
        color: var(--muted) !important;
    }

    [data-testid="stFileUploader"] label,
    [data-testid="stTextInput"] label,
    [data-testid="stTextArea"] label {
        color: var(--text) !important;
        font-weight: 700 !important;
    }

    [data-testid="stFileUploader"] section {
        background: rgba(255, 253, 248, 0.96) !important;
        border: 2px dashed #b9aa92 !important;
        border-radius: 20px !important;
        color: var(--text) !important;
    }

    [data-testid="stFileUploader"] small,
    [data-testid="stFileUploader"] span,
    [data-testid="stFileUploader"] div {
        color: var(--text) !important;
    }

    [data-testid="stTextInput"] input,
    [data-testid="stTextArea"] textarea {
        background: var(--surface) !important;
        color: var(--text) !important;
        border: 1.5px solid var(--border) !important;
        border-radius: 16px !important;
    }

    [data-testid="stTextInput"] input::placeholder,
    [data-testid="stTextArea"] textarea::placeholder {
        color: #7d8b84 !important;
    }

    [data-testid="stButton"] button {
        background: linear-gradient(135deg, #214f45 0%, #2c6a5c 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
        border: none !important;
        border-radius: 16px !important;
        font-weight: 700 !important;
        min-height: 3rem !important;
        box-shadow: 0 12px 24px rgba(33, 79, 69, 0.18);
    }

    [data-testid="stButton"] button:hover {
        background: linear-gradient(135deg, #1b443b 0%, #24574b 100%) !important;
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stButton"] button p,
    [data-testid="stButton"] button span,
    [data-testid="stButton"] button div {
        color: #ffffff !important;
        -webkit-text-fill-color: #ffffff !important;
    }

    [data-testid="stMetric"] {
        background: rgba(255, 253, 248, 0.92);
        border: 1px solid var(--border);
        border-radius: 18px;
        padding: 0.8rem 0.95rem;
    }

    [data-testid="stMetricLabel"] p,
    [data-testid="stMetricValue"] {
        color: var(--text) !important;
    }

    .hero {
        background: linear-gradient(135deg, #183830 0%, #2d6758 55%, #c99758 140%);
        border-radius: 30px;
        padding: 2.4rem;
        box-shadow: 0 22px 46px rgba(27, 55, 48, 0.18);
        margin-bottom: 1.5rem;
    }

    .hero-tag {
        color: rgba(255, 255, 255, 0.82) !important;
        font-size: 0.84rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.7rem;
    }

    .hero-title {
        color: #ffffff !important;
        font-size: 2.7rem;
        line-height: 1.08;
        font-weight: 900;
        max-width: 780px;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 12px rgba(63, 54, 110, 0.28);
    }

    .hero-project-name {
        color: #fffafc !important;
        font-size: 1.15rem;
        font-weight: 700;
        letter-spacing: 0.04em;
        margin-bottom: 0.9rem;
        opacity: 0.96;
    }

    .hero-copy {
        color: rgba(255, 255, 255, 0.92) !important;
        font-size: 1rem;
        line-height: 1.75;
        max-width: 760px;
    }

    .panel {
        background: rgba(255, 253, 248, 0.82);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 1.25rem;
        box-shadow: 0 14px 34px rgba(40, 49, 44, 0.08);
        margin-bottom: 1rem;
    }

    .panel-heading {
        color: var(--text) !important;
        font-size: 1.08rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
    }

    .panel-copy {
        color: var(--muted) !important;
        line-height: 1.7;
        font-size: 0.96rem;
    }

    .score-card {
        background: linear-gradient(135deg, #fff2cf 0%, #f0c76c 100%);
        border: 1px solid #e1c17d;
        border-radius: 24px;
        padding: 1.2rem 1.35rem;
        box-shadow: 0 14px 28px rgba(176, 136, 50, 0.16);
        margin-bottom: 1rem;
    }

    .score-label {
        color: #5b4924 !important;
        font-size: 0.82rem;
        text-transform: uppercase;
        letter-spacing: 0.12em;
        margin-bottom: 0.3rem;
    }

    .score-value {
        color: #2e2414 !important;
        font-size: 2.25rem;
        font-weight: 800;
    }

    .content-card {
        border-radius: 22px;
        padding: 1.1rem 1.15rem;
        margin-bottom: 1rem;
        border: 1px solid var(--border);
        background: var(--surface);
        box-shadow: 0 12px 24px rgba(39, 49, 44, 0.06);
    }

    .content-card.positive {
        background: linear-gradient(180deg, #eaf7f1 0%, #fffdf8 100%);
    }

    .content-card.warning {
        background: linear-gradient(180deg, #fff3df 0%, #fffdf8 100%);
    }

    .content-card.neutral {
        background: linear-gradient(180deg, #edf5fb 0%, #fffdf8 100%);
    }

    .card-heading {
        color: var(--text) !important;
        font-size: 1.02rem;
        font-weight: 800;
        margin-bottom: 0.7rem;
    }

    .card-list {
        color: var(--muted) !important;
        margin: 0;
        padding-left: 1.15rem;
        line-height: 1.7;
    }

    .card-list li {
        margin-bottom: 0.45rem;
    }

    .text-shell {
        background: rgba(255, 253, 248, 0.92);
        border: 1px solid var(--border);
        border-radius: 24px;
        padding: 1rem;
        box-shadow: 0 12px 24px rgba(39, 49, 44, 0.06);
    }
    </style>
    """,
    unsafe_allow_html=True,
)

st.markdown(
    """
    <div class="hero">
        <div class="hero-tag">Smart Resume Review</div>
        <div class="hero-title">AI-Based Resume Analyzer and Feedback System</div>
        <div class="hero-project-name">Smart Resume Analyzer</div>
        <div class="hero-copy">
            Upload a PDF or TXT resume to get a clear local review with visible text, practical feedback,
            and an easy-to-understand score.
        </div>
    </div>
    """,
    unsafe_allow_html=True,
)

left_col, right_col = st.columns([0.92, 1.28], gap="large")

with left_col:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-heading">Upload Resume</div>
            <div class="panel-copy">
                Add your resume file and optionally enter the job role you want to target.
                The app will review structure, content quality, and role alignment.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    uploaded_file = st.file_uploader("Resume file", type=["pdf", "txt"])
    job_role = st.text_input("Target job role", placeholder="Example: Software Engineer Intern")
    provider = st.selectbox(
        "Analysis provider",
        options=["Local", "OpenAI", "Gemini"],
        help="Use Local for offline analysis, or select OpenAI/Gemini if you have set the matching API key.",
    )
    model = st.text_input(
        "Model name (optional)",
        placeholder="Examples: gpt-4o-mini or gemini-1.5-flash",
    )
    analyze_clicked = st.button(
        "Analyze Resume",
        type="primary",
        use_container_width=True,
        disabled=uploaded_file is None,
    )
    st.caption(
        "Local mode needs no API key. For AI mode, set `OPENAI_API_KEY` or `GEMINI_API_KEY` in your environment."
    )

with right_col:
    st.markdown(
        """
        <div class="panel">
            <div class="panel-heading">What The App Checks</div>
            <div class="panel-copy">
                Contact details, education, skills, projects or experience, impact with numbers,
                action verbs, and how well your resume fits the selected job role.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    metric_a, metric_b, metric_c = st.columns(3)
    metric_a.metric("Formats", "PDF / TXT")
    metric_b.metric("Mode", "Local")
    metric_c.metric("Output", "Score + Tips")

if analyze_clicked and uploaded_file is not None:
    try:
        with st.spinner("Extracting resume text..."):
            resume_text = extract_resume_text(uploaded_file)

        if not resume_text.strip():
            st.error("No readable text was found in the uploaded file.")
        else:
            selected_provider = provider.lower()
            spinner_text = (
                "Analyzing resume locally..."
                if selected_provider == "local"
                else f"Analyzing resume with {provider}..."
            )

            with st.spinner(spinner_text):
                result = analyze_resume(
                    resume_text,
                    target_role=job_role.strip() or None,
                    provider=selected_provider,
                    model=model.strip() or None,
                )

            score = extract_score(result)
            strengths = extract_section(result, "Strengths")
            weaknesses = extract_section(result, "Weaknesses")
            suggestions = extract_section(result, "Suggestions for Improvement")

            st.markdown("## Analysis Result")

            results_col, text_col = st.columns([1.2, 0.8], gap="large")

            with results_col:
                if score:
                    st.markdown(
                        f"""
                        <div class="score-card">
                            <div class="score-label">Resume Score</div>
                            <div class="score-value">{score}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )

                first_row_a, first_row_b = st.columns(2, gap="medium")
                with first_row_a:
                    render_card("Strengths", strengths, "positive")
                with first_row_b:
                    render_card("Weaknesses", weaknesses, "warning")

                render_card("Suggestions for Improvement", suggestions, "neutral")

            with text_col:
                st.markdown(
                    """
                    <div class="text-shell">
                        <div class="panel-heading">Extracted Resume Text</div>
                        <div class="panel-copy">
                            This is the text pulled from the uploaded file and used in the analysis.
                        </div>
                    </div>
                    """,
                    unsafe_allow_html=True,
                )
                st.text_area(
                    "Resume text",
                    resume_text,
                    height=380,
                    label_visibility="collapsed",
                )

    except ValueError as exc:
        st.error(str(exc))
    except Exception as exc:
        st.error(f"Something went wrong while analyzing the resume: {exc}")
