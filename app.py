# my-man-jules/app.py

import os
from fastapi import FastAPI
from fastapi.responses import HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from dotenv import load_dotenv

from genai_processors import content_api, processor, streams
from kramer.agent import KramerAgent

load_dotenv()

app = FastAPI()
app.mount("/static", StaticFiles(directory="static"), name="static")

class QueryRequest(BaseModel):
    query: str

@app.get("/", response_class=HTMLResponse)
async def read_root():
    with open("static/index.html") as f:
        return HTMLResponse(content=f.read(), status_code=200)

@app.post("/process")
async def process_query(request: QueryRequest):
    api_key = os.environ.get("GOOGLE_API_KEY")
    if not api_key or api_key == "YOUR_API_KEY_HERE":
        async def error_stream():
            yield "ERROR: GOOGLE_API_KEY environment variable not set on the server."
        return StreamingResponse(error_stream(), media_type="text/plain; charset=utf-8")

    agent = KramerAgent(api_key=api_key)
    input_stream = streams.stream_content([content_api.ProcessorPart(request.query)])

    async def response_generator():
        async for part in agent(input_stream):
            if part.substream_name == "status":
                yield f"{part.text}\n"
            else:
                yield part.text

    return StreamingResponse(response_generator(), media_type="text/plain; charset=utf-8")
