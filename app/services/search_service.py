from azure.core.credentials import AzureKeyCredential
from azure.search.documents import SearchClient
from azure.search.documents.models import VectorizedQuery
from app.services.openai_service import OpenAIService
import logging

from app.config import (
    AZURE_SEARCH_SERVICE_ENDPOINT,
    AZURE_SEARCH_INDEX_NAME, 
    AZURE_SEARCH_API_KEY,
    VECTOR_FIELD_NAME,
)

class SearchService:
    def __init__(self):
        """Initialize the search service with configuration from environment variables"""
        self.endpoint = AZURE_SEARCH_SERVICE_ENDPOINT
        self.key = AZURE_SEARCH_API_KEY
        self.index_name = AZURE_SEARCH_INDEX_NAME
        self.vector_field_name = VECTOR_FIELD_NAME
        
        self.search_client = SearchClient(
            endpoint=self.endpoint,
            index_name=self.index_name,
            credential=AzureKeyCredential(self.key)
        )

        self.openai_service = OpenAIService()
    
    def vector_search(self, query_text, top=3):
        """
        Perform a vector search using Azure AI Search.
        
        Args:
            query_text: The query to search for
            top: Number of results to return
            
        Returns:
            List of search results
        """
    
        query_embedding = self.openai_service.generate_embeddings(query_text)
        
        vector_query = VectorizedQuery(
            vector=query_embedding,
            k_nearest_neighbors=top,
            fields=self.vector_field_name
        )
        try:
            results = self.search_client.search(
                search_text=None,  
                vector_queries=[vector_query],
                select=["title", "chunk", "parent_id"],
                top=top
            )
            print("Successfully retrieved results from vector search")
            return list(results)
        except Exception as e:
            print(f"Vector search error: {str(e)}")
            