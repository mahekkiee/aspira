#networking agent

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from shared.utils import get_secret  # keep your Secret Manager helper
import smtplib
from email.message import EmailMessage
import os

# --- Vertex AI (Gemini) ---
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel

app = FastAPI()

# ----- Vertex init (once) -----
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
vertex_init(project=PROJECT_ID, location=VERTEX_LOCATION)
_gemini = GenerativeModel("gemini-1.5-pro")


class RequestModel(BaseModel):
    user_id: str
    prompt: str      # Raw user message intent
    email: str       # Recipient email address


@app.post("/networking-agent")
async def network(req: RequestModel):
    # 1) Use Gemini to refine the outreach message
    refine_prompt = (
        "Polish and personalize this outreach message for a professional context. "
        "Keep it warm, concise, and actionable:\n\n"
        f"{req.prompt}"
    )
    try:
        gen = _gemini.generate_content(refine_prompt)
        polished = (gen.text or "").strip() or req.prompt
    except Exception:
        polished = req.prompt

    # 2) Send polished message via SMTP (API key from Secret Manager)
    smtp_key = get_secret("SMTP_API_KEY")
    msg = EmailMessage()
    msg["Subject"] = "Aspira Networking Invitation"
    msg["From"] = "no-reply@aspira.ai"
    msg["To"] = req.email
    msg.set_content(polished)

    try:
        with smtplib.SMTP("smtp.example.com", 587, timeout=20) as server:
            server.starttls()
            server.login("apikey", smtp_key)
            server.send_message(msg)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    return {"status": "sent", "email": req.email, "message": polished}