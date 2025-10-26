"""
Vertex AI Vector Search Tools for ADK

This module ingests and queries enterprise documents using Google Cloud Vertex AI Vector Search,
and is designed to be wrapped as ADK tools/actions.
"""

import os
from typing import List, Optional
import vertexai

from google.cloud import aiplatform_v1
from google.genai import Client as GenAIClient
from google.genai.types import EmbedContentConfig
from google.adk.tools import ToolContext, FunctionTool

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
VERTEX_API_KEY = os.getenv("VERTEX_API_KEY")

VECTOR_DEFAULT_MODEL_NAME = os.getenv("VECTOR_DEFAULT_MODEL_NAME")
VECTOR_DEFAULT_EMBED_DIM = int(os.getenv("VECTOR_DEFAULT_EMBED_DIM"))
VECTOR_DEFAULT_INDEX_ENDPOINT = os.getenv("VECTOR_DEFAULT_INDEX_ENDPOINT")
VECTOR_DEFAULT_DEPLOYED_ID = os.getenv("VECTOR_DEFAULT_DEPLOYED_ID")
VECTOR_DEFAULT_API_ENDPOINT = os.getenv("VECTOR_DEFAULT_API_ENDPOINT")


vertexai.init(project=PROJECT_ID, location=LOCATION)
genai_client = GenAIClient(api_key=VERTEX_API_KEY)


def embed_texts(texts: List[str], dim: int = VECTOR_DEFAULT_EMBED_DIM) -> List[List[float]]:
    """Generate embeddings for a list of texts using Gemini embedding model."""
    resp = genai_client.models.embed_content(
        model=VECTOR_DEFAULT_MODEL_NAME,
        contents=texts,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",
            output_dimensionality=dim
        ),
    )
    return [e.values for e in resp.embeddings]


def _execute_vector_search(query_embedding: List[float], k: int):
    """Execute a vector search query against the index."""
    client_options = {"api_endpoint": VECTOR_DEFAULT_API_ENDPOINT}
    vector_search_client = aiplatform_v1.MatchServiceClient(
        client_options=client_options,
    )
    
    datapoint = aiplatform_v1.IndexDatapoint(feature_vector=query_embedding)
    
    query = aiplatform_v1.FindNeighborsRequest.Query(
        datapoint=datapoint,
        neighbor_count=k
    )
    
    request = aiplatform_v1.FindNeighborsRequest(
        index_endpoint=VECTOR_DEFAULT_INDEX_ENDPOINT,
        deployed_index_id=VECTOR_DEFAULT_DEPLOYED_ID,
        queries=[query],
        return_full_datapoint=True,
    )
    
    return vector_search_client.find_neighbors(request)


def _extract_content_from_response(response) -> List[str]:
    """Extract only the text content from vector search response."""
    content_chunks = []
    
    if not response.nearest_neighbors or not response.nearest_neighbors[0].neighbors:
        return content_chunks
    
    for match in response.nearest_neighbors[0].neighbors:
        # Try to get content from restricts first
        content = None
        if hasattr(match.datapoint, 'restricts') and match.datapoint.restricts:
            for restrict in match.datapoint.restricts:
                if restrict.namespace == "content" and restrict.allow_list:
                    content = restrict.allow_list[0]
                    break
        
        # If not found in restricts, try crowding_tag
        if not content and hasattr(match.datapoint, 'crowding_tag') and match.datapoint.crowding_tag:
            crowding_attr = match.datapoint.crowding_tag.crowding_attribute
            if crowding_attr and crowding_attr != "0":
                content = crowding_attr
        
        if content:
            content_chunks.append(content)
    
    return content_chunks

# ADK Tool Function
def retrieve_documents(
    query: str,
    num_results: int = 5
) -> str:
    """
    Retrieve relevant document chunks from the Vector Search index.
    
    Args:
        query: The search query text (e.g., "What is vCare?")
        num_results: Number of chunks to retrieve (default: 5)
    
    Returns:
        String containing the retrieved document chunks, separated by newlines.
        Returns error message if retrieval fails.
    """
    try:
        # Generate query embedding
        query_embedding = embed_texts([query])[0]
        
        # Execute vector search
        response = _execute_vector_search(query_embedding, num_results)
        
        # Extract text chunks
        chunks = _extract_content_from_response(response)
        
        if not chunks:
            return "No relevant documents found for the query."
        
        # Return chunks separated by double newlines
        return "\n\n".join(chunks)
    
    except Exception as e:
        return f"Error retrieving documents: {str(e)}"


query_documents_tool = FunctionTool(retrieve_documents)