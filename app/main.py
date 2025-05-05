import uvicorn
from fastapi import FastAPI
from app.api.router import api_router
from app.config import API_HOST, API_PORT, DEBUG

# Create FastAPI app
app = FastAPI(title="Azure RAG Search API")

# Include API router
app.include_router(api_router)

@app.get("/")
async def root():
    return {"message": "Azure RAG Chat API is running. Use /api endpoints to interact."}

if __name__ == "__main__":
    uvicorn.run("app.main:app", host=API_HOST, port=API_PORT, reload=DEBUG)

