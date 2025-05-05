from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from datetime import datetime
import uuid

class ChatRequest(BaseModel):
    """Simplified model for a chat request"""
    prompt: str
    conversation_id: Optional[str] = None
    user_id: str = Field(..., description="User identifier")

class ChatResponse(BaseModel):
    """Simplified model for a chat response"""
    response: str
    conversation_id: str

class ConversationDocument(BaseModel):
    """Model for a conversation document to be stored in Cosmos DB"""
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    messages: List[Dict[str, str]] 

class ConversationsRequest(BaseModel):
    """Model for a request to retrieve conversations"""
    user_id: str = Field(..., description="User identifier")