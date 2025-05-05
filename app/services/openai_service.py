from openai import AzureOpenAI
from typing import List, Dict, Any
import os

from app.config import (
    AZURE_OPENAI_API_KEY,
    AZURE_OPENAI_ENDPOINT,
    AZURE_OPENAI_MODEL,
    AZURE_OPENAI_API_VERSION,
    AZURE_OPENAI_EMBEDDING_DEPLOYMENT
)

class OpenAIService:
    def __init__(self):
        """Initialize the OpenAI service with configuration from environment variables"""
        self.api_key = AZURE_OPENAI_API_KEY
        self.endpoint = AZURE_OPENAI_ENDPOINT
        self.model = AZURE_OPENAI_MODEL
        self.api_version = AZURE_OPENAI_API_VERSION
        self.embedding_deployment = AZURE_OPENAI_EMBEDDING_DEPLOYMENT
      
        self.client = AzureOpenAI(
            api_key=self.api_key,
            api_version=self.api_version,
            azure_endpoint=self.endpoint 
        )
    
    def generate_response(self, messages: List[Dict[str, str]], temperature: float = 0.7, max_tokens: int = 800) -> str:
        """
        Generate a response using Azure OpenAI.
        
        Args:
            messages: List of message objects with role and content
            temperature: Controls randomness (0-1)
            max_tokens: Maximum number of tokens to generate
            
        Returns:
            The generated response text
        """
        try:
            # If model isn't set, try to use a default model
            model_name = self.model
            
            response = self.client.chat.completions.create(
                model=model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                n=1
            )
            return response.choices[0].message.content
        
        except Exception as e:
            print(f"Error generating response: {str(e)}")
            return f"I'm sorry, but I encountered an error generating a response. Error: {str(e)}"
    
    def generate_embeddings(self, text: str) -> List[float]:
        """
        Generate embeddings for the given text using Azure OpenAI.
        
        Args:
            text: The text to generate embeddings for
            
        Returns:
            The embedding vector
        """
        try:
            # Use the embedding model from config
            print(f"Generating embeddings with model: {self.embedding_deployment}")
            
            response = self.client.embeddings.create(
                model=self.embedding_deployment,
                input=text
            )
            
            return response.data[0].embedding
        
        except Exception as e:
            print(f"Error generating embeddings: {str(e)}")
            return None