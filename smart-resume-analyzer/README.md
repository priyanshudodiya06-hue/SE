# Smart Resume Analyzer

AI-Based Resume Analyzer and Feedback System built with Streamlit and a local rule-based analyzer.

## Features

- Upload resume in PDF or TXT format
- Extract text from the file
- Analyze the resume locally without any API key
- Show:
  - Strengths
  - Weaknesses
  - Suggestions
  - Score out of 10
- Optional target job role input

## Tech Stack

- Frontend: Streamlit
- Analysis Engine: Local Python rule-based analyzer
- PDF parsing: PyPDF2

## Setup

1. Create and activate a virtual environment.
2. Install dependencies:

```bash
pip install -r requirements.txt
```

## Run the Project

```bash
streamlit run app.py
```

## Project Flow

User uploads resume -> text is extracted -> local analyzer reviews content -> feedback is displayed

## Suggested Testing

- Good resume
- Weak resume
- Empty file
- PDF with very little text
- TXT resume
