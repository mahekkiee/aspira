#progress tracker

from fastapi import FastAPI
from pydantic import BaseModel
from shared.utils import init_firestore
import os

# --- Vertex AI (Gemini) ---
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel

app = FastAPI()
db = init_firestore()

# ----- Vertex init (once) -----
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")
vertex_init(project=PROJECT_ID, location=VERTEX_LOCATION)
_gemini = GenerativeModel("gemini-1.5-pro")


class RequestModel(BaseModel):
    user_id: str
    action: str       # "get" or "update"
    progress: dict | None = None


@app.post("/progress-tracker")
async def track(req: RequestModel):
    doc_ref = db.collection("progress").document(req.user_id)

    if req.action == "update" and req.progress:
        doc_ref.set(req.progress, merge=True)
        stored = req.progress
        status = "updated"
    else:
        snapshot = doc_ref.get()
        stored = snapshot.to_dict() or {}
        status = "fetched"

    # Generate an insight using Gemini
    insight_prompt = (
        f"User progress details: {stored}\n\n"
        "Provide 1 motivational insight and 1 next best step. "
        "Keep it in two short bullet points."
    )
    try:
        gen = _gemini.generate_content(insight_prompt)
        insight = (gen.text or "").strip()
    except Exception:
        insight = ""

    return {"status": status, "progress": stored, "insight": insight}