from fastapi import APIRouter, HTTPException, Depends, Query
import uuid
from datetime import datetime
from typing import Dict, List, Optional

from app.models.chat import ChatRequest, ChatResponse, ConversationsRequest
from app.services.search_service import SearchService
from app.services.openai_service import OpenAIService
from app.services.cosmos_service import CosmosDBService

router = APIRouter()

search_service = SearchService()
openai_service = OpenAIService()
cosmos_service = CosmosDBService()

@router.get("/")
async def root():
    """Health check endpoint"""
    return {"message": "RAG Chat API is running"}

@router.post("/openai", response_model=ChatResponse)
async def chat(request: ChatRequest):
    """
    Process a chat request with RAG.
    """
    try:
        if not request.user_id:
            raise HTTPException(status_code=400, detail="user_id is required")
            
        user_query = request.prompt
        
        conversation_id = request.conversation_id or str(uuid.uuid4())
        
        previous_messages = []
        if request.conversation_id:
            try:
                conversation = cosmos_service.get_conversation(request.conversation_id)
                if conversation and conversation.get("user_id") == request.user_id:
                    previous_messages = conversation.get("messages", [])
                    print(f"Loaded {len(previous_messages)} previous messages from conversation {request.conversation_id}")
                else:
                    # Either conversation not found or user_id mismatch
                    if conversation:
                        print(f"User ID mismatch for conversation {request.conversation_id}")
                        # Create a new conversation_id since this is not the conversation owner
                        conversation_id = str(uuid.uuid4())
                    else:
                        print(f"Conversation {request.conversation_id} not found")
            except Exception as e:
                print(f"Error loading previous conversation: {str(e)}")
        
        search_results = []
        try:
            search_results = search_service.vector_search(user_query)
            print(f"Found {len(search_results)} search results")
        except Exception as search_error:
            print(f"Search error: {str(search_error)}")
        
        context = ""
        
        for result in search_results:
            content = result.get("chunk", "")
            context += f"{content}\n\n"
        
        system_message = f"""You are a helpful assistant. Use the following context to answer the user's question. 
        If you don't know the answer based on this context, say "I don't have enough information to answer that question."
        
        Context:
        {context}
        """
        
        messages_for_openai = [{"role": "system", "content": system_message}]
        
        # Add previous conversation history (excluding system messages)
        for msg in previous_messages:
            if msg["role"] != "system":
                messages_for_openai.append({"role": msg["role"], "content": msg["content"]})
        
        messages_for_openai.append({"role": "user", "content": user_query})
        
        ai_response = openai_service.generate_response(messages_for_openai)
        
        current_timestamp = datetime.utcnow().isoformat()
        
        if previous_messages:
            # Add to existing conversation
            messages = previous_messages.copy()
            messages.append({
                "role": "user", 
                "content": user_query,
                "timestamp": current_timestamp
            })
            messages.append({
                "role": "assistant", 
                "content": ai_response,
                "timestamp": current_timestamp
            })
        else:
            # Create a new conversation
            messages = [
                {
                    "role": "user", 
                    "content": user_query,
                    "timestamp": current_timestamp
                },
                {
                    "role": "assistant", 
                    "content": ai_response,
                    "timestamp": current_timestamp
                }
            ]
    
        conversation_data = {
            "id": conversation_id,
            "user_id": str(request.user_id),  # Ensure it's stored as a string
            "messages": messages,
        }
        
        print(f"Saving conversation with ID: {conversation_id} for user: {request.user_id}")
        cosmos_service.save_conversation(conversation_data)
        
        return {
            "response": ai_response,
            "conversation_id": conversation_id
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e)) 
    
@router.get("/conversations")
async def get_conversations(user_id: str):
    """
    Retrieve all conversations for a specific user
    """
    if not user_id:
        raise HTTPException(status_code=400, detail="User ID is required")
    
    try:
        print(f"Fetching conversations for user: {user_id}")
        user_id_str = str(user_id).strip()
        
        # Get conversations with error handling for Unicode issues
        try:
            conversations = cosmos_service.get_conversations_by_user(user_id_str)
            print(f"Retrieved {len(conversations)} conversations from CosmosDB")
            return {"conversations": conversations}
        except UnicodeEncodeError as ue:
            print(f"Unicode encoding error: {str(ue)}")
            return {"conversations": conversations if 'conversations' in locals() else []}
            
    except Exception as e:
        error_msg = f"Error retrieving conversations: {str(e)}"
        if isinstance(e, UnicodeEncodeError):
            error_msg = "Error with special characters in conversations"
        raise HTTPException(status_code=500, detail=error_msg)
