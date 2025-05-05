import azure.cosmos.cosmos_client as cosmos_client
import azure.cosmos.exceptions as exceptions
from azure.cosmos.partition_key import PartitionKey
from typing import Dict, List, Any, Optional
import os

from app.config import (
    COSMOS_ENDPOINT,
    COSMOS_KEY,
    COSMOS_DATABASE,
    COSMOS_CONTAINER
)

class CosmosDBService:
    def __init__(self):
        """Initialize the Cosmos DB service with configuration from environment variables"""
        try:
            self.endpoint = COSMOS_ENDPOINT
            self.key = COSMOS_KEY
            self.database_name = COSMOS_DATABASE
            self.container_name = COSMOS_CONTAINER
            
            print(f"Initializing CosmosDBService with endpoint: {self.endpoint}")
            
            if not self.endpoint or not self.key:
                print("WARNING: Cosmos DB endpoint or key is missing!")
                
            self.client = cosmos_client.CosmosClient(self.endpoint, self.key)
            
            self.database = self._get_or_create_database()
            self.container = self._get_or_create_container()
            
            print("CosmosDBService initialization completed successfully")
            
        except Exception as e:
            print(f"ERROR initializing CosmosDBService: {str(e)}")
            # Still initialize these to avoid NoneType errors, but the service won't work
            self.database = None
            self.container = None
    
    def _get_or_create_database(self):
        """Create the database if it doesn't exist."""
        try:
            return self.client.create_database(id=self.database_name)
        except exceptions.CosmosResourceExistsError:
            return self.client.get_database_client(self.database_name)
    
    def _get_or_create_container(self):
        """Create the container if it doesn't exist."""
        try:
            return self.database.create_container(
                id=self.container_name,
                partition_key=PartitionKey(path="/user_id")
            )
        except exceptions.CosmosResourceExistsError:
            return self.database.get_container_client(self.container_name)
    
    def save_conversation(self, conversation_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Save a conversation to Cosmos DB.
        
        Args:
            conversation_data: Dictionary containing conversation details
            
        Returns:
            The saved item
        """
        try:
            # Ensure user_id is present
            if "user_id" not in conversation_data or not conversation_data["user_id"]:
                raise ValueError("user_id is required for saving conversations")
                
            print(f"Saving conversation with ID: {conversation_data.get('id')} and user_id: {conversation_data.get('user_id')}")
            return self.container.upsert_item(body=conversation_data)
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error saving conversation: {str(e)}")
            raise
    
    def get_conversation(self, conversation_id: str) -> Optional[Dict[str, Any]]:
        """
        Retrieve a specific conversation by ID.
        
        Args:
            conversation_id: The ID of the conversation to retrieve
            
        Returns:
            The conversation document or None if not found
        """
        try:
            query = f"SELECT * FROM c WHERE c.id = '{conversation_id}'"
            items = list(self.container.query_items(query=query, enable_cross_partition_query=True))
            
            if items:
                return items[0]
            return None
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error retrieving conversation: {str(e)}")
            return None
    
    def get_conversations_by_user(self, user_id: str) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations for a specific user.
        
        Args:
            user_id: The ID of the user
            
        Returns:
            List of conversation documents
        """
        try:
            print(f"Fetching conversations for user_id: {user_id}")
            
            # Try using string conversion on user_id to ensure consistent format
            user_id = str(user_id).strip()
            
            # First try with partition key (more efficient)
            try:
                query = "SELECT * FROM c WHERE c.user_id = @userId ORDER BY c._ts DESC"
                params = [{"name": "@userId", "value": user_id}]
                
                items = list(self.container.query_items(
                    query=query,
                    parameters=params,
                    partition_key=user_id
                ))
                
                print(f"Found {len(items)} conversations with partition key query")
                
                # Clean messages to avoid encoding issues
                try:
                    for item in items:
                        if 'messages' in item:
                            # Just for debugging, don't modify the actual data
                            pass
                except Exception as e:
                    print(f"Warning: Error handling message content: {str(e)}")
                
                return items
                
            except Exception as partition_error:
                print(f"Partition key query failed: {str(partition_error)}. Falling back to cross-partition query.")
                
                # Fall back to cross-partition query
                query = "SELECT * FROM c WHERE c.user_id = @userId ORDER BY c._ts DESC"
                params = [{"name": "@userId", "value": user_id}]
                
                items = list(self.container.query_items(
                    query=query,
                    parameters=params,
                    enable_cross_partition_query=True
                ))
                
                print(f"Found {len(items)} conversations with cross-partition query")
                
                # Clean messages to avoid encoding issues
                try:
                    for item in items:
                        if 'messages' in item:
                            # Just for debugging, don't modify the actual data
                            pass
                except Exception as e:
                    print(f"Warning: Error handling message content: {str(e)}")
                
                return items
            
        except Exception as e:
            print(f"Error retrieving user conversations: {str(e)}")
            # Return empty list instead of crashing
            return []
    
    def get_all_conversations(self, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Retrieve all conversations (for debugging purposes).
        
        Args:
            limit: Maximum number of conversations to retrieve
            
        Returns:
            List of conversation documents
        """
        try:
            query = f"SELECT TOP {limit} * FROM c ORDER BY c._ts DESC"
            items = list(self.container.query_items(
                query=query,
                enable_cross_partition_query=True
            ))
            
            return items
            
        except exceptions.CosmosHttpResponseError as e:
            print(f"Error retrieving all conversations: {str(e)}")
            return []
    