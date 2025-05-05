from fastapi import APIRouter
from app.api.endpoints import router as chat_router

api_router = APIRouter()

# Include endpoints router with prefix
api_router.include_router(chat_router, prefix="/api", tags=["chat"]) 