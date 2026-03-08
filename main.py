import os
import json
import re
import io
import tempfile
from pathlib import Path
from typing import Optional
from datetime import datetime, timedelta
from collections import defaultdict

import anthropic
from fastapi import FastAPI, File, UploadFile, Form, Request, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import uvicorn

# File parsing libraries
try:
    import pdfplumber
    PDF_SUPPORT = True
except ImportError:
    PDF_SUPPORT = False

try:
    from docx import Document
    DOCX_SUPPORT = True
except ImportError:
    DOCX_SUPPORT = False

app = FastAPI(title="ResumeRank AI - ATS Checker", version="1.0.0")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Rate limiting storage (in-memory for demo; use Redis in production)
request_counts = defaultdict(lambda: {"count": 0, "reset_time": datetime.now() + timedelta(hours=24)})
FREE_DAILY_LIMIT = 3

def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0]
    return request.client.host

def check_rate_limit(ip: str) -> tuple[bool, int]:
    now = datetime.now()
    data = request_counts[ip]
    if now > data["reset_time"]:
        data["count"] = 0
        data["reset_time"] = now + timedelta(hours=24)
    if data["count"] >= FREE_DAILY_LIMIT:
        return False, 0
    remaining = FREE_DAILY_LIMIT - data["count"]
    return True, remaining

def extract_text_from_pdf(file_bytes: bytes) -> str:
    if not PDF_SUPPORT:
        raise HTTPException(status_code=500, detail="PDF support not installed. Run: pip install pdfplumber")
    with pdfplumber.open(io.BytesIO(file_bytes)) as pdf:
        text = ""
        for page in pdf.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
    return text.strip()

def extract_text_from_docx(file_bytes: bytes) -> str:
    if not DOCX_SUPPORT:
        raise HTTPException(status_code=500, detail="DOCX support not installed. Run: pip install python-docx")
    doc = Document(io.BytesIO(file_bytes))
    paragraphs = [para.text for para in doc.paragraphs if para.text.strip()]
    return "\n".join(paragraphs)

def extract_text_from_txt(file_bytes: bytes) -> str:
    return file_bytes.decode("utf-8", errors="ignore")

def extract_resume_text(file_bytes: bytes, filename: str) -> str:
    ext = Path(filename).suffix.lower()
    if ext == ".pdf":
        return extract_text_from_pdf(file_bytes)
    elif ext in [".docx", ".doc"]:
        return extract_text_from_docx(file_bytes)
    elif ext == ".txt":
        return extract_text_from_txt(file_bytes)
    else:
        raise HTTPException(status_code=400, detail=f"Unsupported file type: {ext}")

def analyze_ats_with_claude(resume_text: str, job_description: str, is_pro: bool = False) -> dict:
    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        # Demo mode - return mock data
        return generate_demo_result(resume_text, job_description)

    client = anthropic.Anthropic(api_key=api_key)

    detail_level = "comprehensive with actionable insights" if is_pro else "concise with top 5 key suggestions"

    prompt = f"""You are an expert ATS (Applicant Tracking System) analyzer and career coach. Analyze the resume against the job description and provide a detailed ATS compatibility report.

RESUME TEXT:
{resume_text[:4000]}

JOB DESCRIPTION:
{job_description[:2000]}

Analyze and respond ONLY with a valid JSON object in this exact structure:
{{
  "ats_score": <integer 0-100>,
  "grade": "<A+/A/A-/B+/B/B-/C+/C/D/F>",
  "summary": "<2-3 sentence overall assessment>",
  "keyword_match": {{
    "matched_keywords": ["<keyword1>", "<keyword2>", ...],
    "missing_keywords": ["<keyword1>", "<keyword2>", ...],
    "match_percentage": <integer 0-100>
  }},
  "sections_analysis": {{
    "contact_info": {{"score": <0-100>, "status": "<good/warning/missing>", "note": "<brief note>"}},
    "work_experience": {{"score": <0-100>, "status": "<good/warning/missing>", "note": "<brief note>"}},
    "education": {{"score": <0-100>, "status": "<good/warning/missing>", "note": "<brief note>"}},
    "skills": {{"score": <0-100>, "status": "<good/warning/missing>", "note": "<brief note>"}},
    "formatting": {{"score": <0-100>, "status": "<good/warning/missing>", "note": "<brief note>"}}
  }},
  "suggestions": [
    {{
      "priority": "<high/medium/low>",
      "category": "<Keywords/Formatting/Content/Skills/Experience>",
      "title": "<short title>",
      "description": "<actionable suggestion>",
      "example": "<specific example if applicable>"
    }}
  ],
  "strengths": ["<strength1>", "<strength2>", "<strength3>"],
  "quick_wins": ["<quick improvement 1>", "<quick improvement 2>", "<quick improvement 3>"]
}}

Provide {detail_level}. Be specific and actionable."""

    message = client.messages.create(
        model="claude-opus-4-5",
        max_tokens=2000,
        messages=[{"role": "user", "content": prompt}]
    )

    response_text = message.content[0].text.strip()
    # Extract JSON from response
    json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
    if json_match:
        return json.loads(json_match.group())
    return json.loads(response_text)

def generate_demo_result(resume_text: str, job_description: str) -> dict:
    """Demo mode when no API key is set"""
    words_in_resume = set(resume_text.lower().split())
    words_in_jd = set(job_description.lower().split())
    
    common = words_in_resume & words_in_jd
    score = min(int(len(common) / max(len(words_in_jd), 1) * 200), 78)

    return {
        "ats_score": score,
        "grade": "B+" if score >= 75 else "B" if score >= 65 else "C+",
        "summary": "Demo mode: Set ANTHROPIC_API_KEY for real AI analysis. Your resume shows potential but needs keyword optimization to pass ATS filters effectively.",
        "keyword_match": {
            "matched_keywords": list(common)[:8],
            "missing_keywords": ["Python", "Machine Learning", "Data Analysis", "Agile", "Team Leadership"],
            "match_percentage": score
        },
        "sections_analysis": {
            "contact_info": {"score": 90, "status": "good", "note": "Contact information present"},
            "work_experience": {"score": 72, "status": "warning", "note": "Add quantifiable achievements"},
            "education": {"score": 85, "status": "good", "note": "Education section looks good"},
            "skills": {"score": 60, "status": "warning", "note": "Add more technical skills from JD"},
            "formatting": {"score": 80, "status": "good", "note": "Clean formatting detected"}
        },
        "suggestions": [
            {"priority": "high", "category": "Keywords", "title": "Add Missing Technical Keywords", "description": "Include key terms from the job description that are missing in your resume.", "example": "Add 'Python', 'Machine Learning', 'Data Analysis' to your skills section"},
            {"priority": "high", "category": "Content", "title": "Quantify Achievements", "description": "Replace vague descriptions with specific numbers and metrics.", "example": "Changed 'Improved sales' to 'Increased sales by 35% in Q3 2023'"},
            {"priority": "medium", "category": "Formatting", "title": "Use Standard Section Headers", "description": "ATS systems look for standard headers like 'Work Experience', 'Education', 'Skills'.", "example": "Rename 'My Background' to 'Work Experience'"},
            {"priority": "medium", "category": "Skills", "title": "Create Dedicated Skills Section", "description": "Have a dedicated skills section with a bullet-point list of technical competencies.", "example": "Skills: Python, SQL, Tableau, Machine Learning, Data Visualization"},
            {"priority": "low", "category": "Content", "title": "Add Action Verbs", "description": "Start each bullet point with a strong action verb.", "example": "Led, Developed, Implemented, Optimized, Delivered"}
        ],
        "strengths": ["Resume has clear structure", "Work experience is well-documented", "Education credentials are prominently displayed"],
        "quick_wins": ["Add the job title from the posting to your resume header", "Include a professional summary tailored to this role", "Add 5-10 keywords from the job description to your skills section"]
    }


@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

@app.get("/pricing", response_class=HTMLResponse)
async def pricing(request: Request):
    return templates.TemplateResponse("pricing.html", {"request": request})

@app.post("/analyze")
async def analyze_resume(
    request: Request,
    resume: UploadFile = File(...),
    job_description: str = Form(...),
    pro_token: Optional[str] = Form(None)
):
    # Validate file
    allowed_extensions = {".pdf", ".doc", ".docx", ".txt"}
    file_ext = Path(resume.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Please upload: {', '.join(allowed_extensions)}"
        )

    # Check file size (5MB limit for free, 15MB for pro)
    max_size = 15 * 1024 * 1024 if pro_token else 5 * 1024 * 1024
    file_bytes = await resume.read()
    if len(file_bytes) > max_size:
        raise HTTPException(status_code=400, detail="File too large. Max 5MB for free users.")

    # Rate limiting (skip for pro users)
    ip = get_client_ip(request)
    is_pro = bool(pro_token and pro_token == os.environ.get("PRO_TOKEN", "demo_pro"))

    if not is_pro:
        allowed, remaining = check_rate_limit(ip)
        if not allowed:
            raise HTTPException(
                status_code=429,
                detail="Daily limit reached. Upgrade to Pro for unlimited checks."
            )
        request_counts[ip]["count"] += 1

    # Extract text
    try:
        resume_text = extract_resume_text(file_bytes, resume.filename)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read file: {str(e)}")

    if len(resume_text.strip()) < 50:
        raise HTTPException(status_code=400, detail="Resume appears to be empty or unreadable.")

    # Validate job description
    if len(job_description.strip()) < 30:
        raise HTTPException(status_code=400, detail="Job description is too short. Please provide more details.")

    # Analyze with Claude
    try:
        result = analyze_ats_with_claude(resume_text, job_description, is_pro)
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Failed to parse AI response. Please try again.")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

    result["filename"] = resume.filename
    result["is_pro"] = is_pro
    result["remaining_checks"] = FREE_DAILY_LIMIT - request_counts[ip]["count"] if not is_pro else "unlimited"

    return JSONResponse(content=result)


@app.get("/health")
async def health():
    return {"status": "ok", "api_key_set": bool(os.environ.get("ANTHROPIC_API_KEY"))}

@app.get("/privacy", response_class=HTMLResponse)
async def privacy(request: Request):
    return templates.TemplateResponse("privacy.html", {"request": request})

@app.get("/terms", response_class=HTMLResponse)
async def terms(request: Request):
    return templates.TemplateResponse("terms.html", {"request": request})

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
