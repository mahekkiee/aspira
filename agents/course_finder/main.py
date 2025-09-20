# main.py
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from googleapiclient.discovery import build
from typing import List, Dict
import os

# --- Vertex AI (Gemini) ---
from vertexai import init as vertex_init
from vertexai.generative_models import GenerativeModel

# --- Project helpers ---
from shared.utils import get_secret  # unchanged: pulls from Secret Manager

app = FastAPI(title="Course Finder Agent")

# ----------------------------
# Vertex init + model singleton
# ----------------------------
PROJECT_ID = os.getenv("GCP_PROJECT") or os.getenv("GOOGLE_CLOUD_PROJECT")
# Gemini is most reliable in us-central1; you can change if needed
VERTEX_LOCATION = os.getenv("VERTEX_LOCATION", "us-central1")

# initialize Vertex once at import time (Cloud Run container startup)
vertex_init(project=PROJECT_ID, location=VERTEX_LOCATION)
_gemini_model = GenerativeModel("gemini-1.5-pro")


def summarize_with_gemini(text: str) -> str:
    """
    Summarize video description in one sentence using Vertex Gemini.
    Keeps calls simple and robust for hackathon reliability.
    """
    if not text:
        return ""
    prompt = (
        "Summarize the following YouTube course/video description in ONE crisp sentence, "
        "focusing on what a learner will gain:\n\n"
        f"{text}"
    )
    try:
        resp = _gemini_model.generate_content(prompt)
        return (resp.text or "").strip()
    except Exception as e:
        # Fail soft: return empty summary on model errors
        # (You can log e via Cloud Logging if you want)
        return ""


# ----------------------------
# API models
# ----------------------------
class RequestModel(BaseModel):
    user_id: str
    prompt: str
    max_results: int = 5  # optional override


# ----------------------------
# Health check
# ----------------------------
@app.get("/ping")
def ping():
    return {"ok": True}


# ----------------------------
# Main endpoint
# ----------------------------
@app.post("/course-finder")
async def find_courses(req: RequestModel) -> Dict[str, List[Dict[str, str]]]:
    """
    1) Reads YT API key from Secret Manager via shared.utils.get_secret
    2) Searches YouTube for relevant videos/playlists
    3) Summarizes each result with Gemini
    """
    # 1) YouTube client
    try:
        api_key = get_secret("youtube-api-key")
        if not api_key:
            raise RuntimeError("youtube-api-key secret is empty or missing")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Secret error: {e}")

    try:
        yt = build("youtube", "v3", developerKey=api_key)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube client init failed: {e}")

    # 2) Search videos/playlists for the given prompt
    try:
        search = (
            yt.search()
            .list(
                q=req.prompt,
                part="snippet",
                maxResults=max(1, min(req.max_results, 10)),
                type="video",  # keep to 'video' for simpler demo; 'playlist' also possible
                safeSearch="none",
            )
        )
        response = search.execute()
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"YouTube search failed: {e}")

    # 3) Build results + summarize with Gemini
    courses: List[Dict[str, str]] = []
    for item in response.get("items", []):
        snippet = item.get("snippet", {}) or {}
        video_id = (item.get("id", {}) or {}).get("videoId")
        title = snippet.get("title") or "Untitled"
        description = snippet.get("description") or ""
        url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

        summary = summarize_with_gemini(description)

        courses.append(
            {
                "title": title,
                "url": url,
                "summary": summary,
            }
        )

    return {"courses": courses}