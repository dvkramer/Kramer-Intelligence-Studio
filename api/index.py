# api/index.py
import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from .kramer.orchestrator import Orchestrator

app = FastAPI()

class QueryRequest(BaseModel):
    query: str

@app.post("/api/run")
async def run_kramer(request: QueryRequest):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key:
        return StreamingResponse(iter(["ERROR: GOOGLE_API_KEY not set."]), media_type="text/plain")

    orchestrator = Orchestrator(api_key=api_key)
    return StreamingResponse(orchestrator.run(request.query), media_type="text/event-stream")

# Add a root endpoint for simple health checks
@app.get("/")
def read_root():
    return {"status": "KRAMER API is running"}
