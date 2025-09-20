#roadmap maker

from fastapi import FastAPI
from pydantic import BaseModel
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
    prompt: str


@app.post("/roadmap-maker")
async def roadmap(req: RequestModel):
    instruction = (
        "Create a detailed, step-by-step learning roadmap for the goal below. "
        "Break it into weeks, list concrete resources, and add estimated durations "
        "(in hours). Keep it compact and practical.\n\n"
        f"GOAL:\n{req.prompt}"
    )
    try:
        prediction = _gemini.generate_content(instruction)
        roadmap_text = (prediction.text or "").strip()
    except Exception:
        roadmap_text = ""

    return {"roadmap": roadmap_text}