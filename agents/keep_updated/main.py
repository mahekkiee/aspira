#keep_updated
from fastapi import FastAPI
from pydantic import BaseModel
from shared.utils import init_firestore  # keep your Firestore helper
import requests
from bs4 import BeautifulSoup
import os

# --- Vertex AI (Gemini) ---
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel

app = FastAPI()
db = init_firestore()

# ----- Vertex init (once) -----
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")  # reliable for Gemini
vertex_init(project=PROJECT_ID, location=VERTEX_LOCATION)
_gemini = GenerativeModel("gemini-1.5-pro")


class RequestModel(BaseModel):
    user_id: str
    prompt: str   # URL to monitor or topic


@app.post("/keep-updated")
async def keep_updated(req: RequestModel):
    # 1) Scrape headlines from the provided URL
    resp = requests.get(req.prompt, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    headlines = [h.get_text().strip() for h in soup.select("h2")][:5]
    combined = "\n".join(headlines) if headlines else "No headlines found."

    # 2) Summarize with Gemini
    summary_prompt = (
        "Summarize these headlines into exactly three concise bullet points:\n\n"
        f"{combined}"
    )
    try:
        gen = _gemini.generate_content(summary_prompt)
        summary = (gen.text or "").strip()
    except Exception:
        summary = ""

    # 3) Store raw + summary in Firestore
    db.collection("updates").document(req.user_id).set(
        {"headlines": headlines, "summary": summary}, merge=True
    )

    return {"headlines": headlines, "summary": summary}