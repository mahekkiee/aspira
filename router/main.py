from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
import httpx
from shared.utils import get_secret

app = FastAPI()

class PromptRequest(BaseModel):
    user_id: str
    prompt: str

# Map intents to agent URLs
AGENTS = {
    "course_finder": "https://REGION-run.googleapis.com/course-finder",
    "roadmap_maker": "https://…/roadmap-maker",
    "progress_tracker": "https://…/progress-tracker",
    "networking_agent": "https://…/networking-agent",
    "keep_updated": "https://…/keep-updated"
}

@app.post("/execute-prompt")
async def execute(request: PromptRequest):
    results = {}
    async with httpx.AsyncClient() as client:
        for name, url in AGENTS.items():
            resp = await client.post(url, json=request.dict())
            if resp.status_code != 200:
                raise HTTPException(status_code=500, detail=f"{name} failed")
            results[name] = resp.json()
    return {"user_id": request.user_id, "results": results}
