import uvicorn
from fastapi import FastAPI, Request
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse
from app.api.router import api_router
from app.config import API_HOST, API_PORT, DEBUG
import os
from pathlib import Path

# Create FastAPI app
app = FastAPI(title="Azure RAG Search API")

# Include API router
app.include_router(api_router)

# Set up template directory
BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))

@app.get("/", response_class=HTMLResponse)
async def chat_ui(request: Request):
    """Serve the chat UI"""
    return templates.TemplateResponse("chat.html", {"request": request})

@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"message": "Azure RAG Chat API is running. Use /api endpoints to interact."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG)

