"""
Google Cloud Storage (GCS) Bucket Management Tools for ADK

This module provides tools for creating and listing GCS buckets to be used with the Agent Development Kit (ADK).
"""
import os
from google.cloud import storage
from google.api_core.exceptions import GoogleAPIError
from google.adk.tools import ToolContext, FunctionTool
from typing import Dict, Any, Optional

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
GCS_LIST_BUCKETS_MAX_RESULTS = int(os.getenv("GCS_LIST_BUCKETS_MAX_RESULTS"))
GCS_LIST_BLOBS_MAX_RESULTS = int(os.getenv("GCS_LIST_BLOBS_MAX_RESULTS"))
GCS_DEFAULT_CONTENT_TYPE = os.getenv("GCS_DEFAULT_CONTENT_TYPE")


# Initialize the GCS client
client = storage.Client(project=PROJECT_ID)

def list_gcs_buckets(
    prefix: Optional[str] = None,
    max_results: Optional[int] = None
    ) -> Dict[str, Any]:
    """
    Lists Google Cloud Storage buckets in the configured project.
    
    Args:
        prefix: Optional prefix to filter buckets by name
        max_results: Maximum number of results to return (default: 50)
        
    Returns:
        A dictionary containing the list of buckets
    """
    if max_results is None:
        max_results = GCS_LIST_BUCKETS_MAX_RESULTS
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # List the buckets with optional filtering
        bucket_iterator = client.list_buckets(prefix=prefix, max_results=max_results)
        
        bucket_list = []
        for bucket in bucket_iterator:
            bucket_list.append({
                "name": bucket.name,
                "location": bucket.location,
                "storage_class": bucket.storage_class,
                "created": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if hasattr(bucket, "updated") and bucket.updated else None
            })
        
        return {
            "status": "success",
            "buckets": bucket_list,
            "count": len(bucket_list),
            "message": f"Found {len(bucket_list)} bucket(s)" + (f" with prefix '{prefix}'" if prefix else "")
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to list buckets: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def get_bucket_details() -> Dict[str, Any]:
    """
    Gets detailed information about a specific GCS bucket, including a list of all files (blobs).
    
    Args:
        bucket_name: The name of the bucket to get details for
        
    Returns:
        A dictionary containing the bucket details and a list of files
    """
    bucket_name = "cymbal-document"

    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.get_bucket(bucket_name)
        
        # List all blobs in the bucket
        blobs = client.list_blobs(bucket_name)
        blob_list = []
        for blob in blobs:
            blob_list.append({
                "name": blob.name,
                "size": blob.size,
                "content_type": blob.content_type,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "gcs_uri": f"gs://{bucket_name}/{blob.name}",
                "public_url": f"https://storage.googleapis.com/{bucket_name}/{blob.name}"
            })
        
        # Return detailed information
        return {
            "status": "success",
            "bucket": {
                "name": bucket.name,
                "id": bucket.id,
                "project_number": bucket.project_number,
                "location": bucket.location,
                "location_type": bucket.location_type,
                "storage_class": bucket.storage_class,
                "created": bucket.time_created.isoformat() if bucket.time_created else None,
                "updated": bucket.updated.isoformat() if hasattr(bucket, "updated") and bucket.updated else None,
                "versioning_enabled": bucket.versioning_enabled,
                "labels": bucket.labels,
                "requester_pays": bucket.requester_pays,
                "self_link": f"https://storage.googleapis.com/{bucket_name}",
                "etag": bucket.etag,
                "files": blob_list,
                "file_count": len(blob_list)
            },
            "message": f"Successfully retrieved details and {len(blob_list)} file(s) for bucket '{bucket_name}'"
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to get bucket details: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def list_blobs_in_bucket(
    prefix: Optional[str] = None,
    delimiter: Optional[str] = None,
    max_results: Optional[int] = None
) -> Dict[str, Any]:
    """
    Lists blobs (files) in a Google Cloud Storage bucket.
    
    Args:
        bucket_name: The name of the bucket to list blobs from
        prefix: Optional prefix to filter blobs by name
        delimiter: Optional delimiter for hierarchy simulation (e.g., '/' for folders)
        max_results: Maximum number of results to return (default: 100)
        
    Returns:
        A dictionary containing the list of blobs and prefixes (if delimiter is used)
    """
    bucket_name = "cymbal-document"
    
    if max_results is None:
        max_results = GCS_LIST_BLOBS_MAX_RESULTS
    try:
        # Initialize the client
        client = storage.Client(project=PROJECT_ID)
        
        # Get the bucket
        bucket = client.bucket(bucket_name)
        
        # List blobs with optional filtering
        blobs = client.list_blobs(
            bucket_name, 
            prefix=prefix, 
            delimiter=delimiter,
            max_results=max_results
        )
        
        # Process the results
        blob_list = []
        prefix_list = []
        
        # Save actual blobs
        for blob in blobs:
            blob_list.append({
                "name": blob.name,
                "size": blob.size,
                "updated": blob.updated.isoformat() if blob.updated else None,
                "content_type": blob.content_type,
                "public_url": f"https://storage.googleapis.com/{bucket_name}/{blob.name}",
                "gcs_uri": f"gs://{bucket_name}/{blob.name}"
            })
        
        # If using delimiter, also save prefixes (folders)
        if delimiter:
            prefix_list = list(blobs.prefixes)
        
        return {
            "status": "success",
            "bucket_name": bucket_name,
            "blobs": blob_list,
            "prefixes": prefix_list,
            "count": len(blob_list),
            "prefix_count": len(prefix_list),
            "message": f"Found {len(blob_list)} file(s) and {len(prefix_list)} folder(s) in bucket '{bucket_name}'"
                      + (f" with prefix '{prefix}'" if prefix else "")
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to list files in bucket: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

def upload_file_to_gcs(
    tool_context: ToolContext,
    file_artifact_name: str,
    destination_blob_name: Optional[str] = None,
    content_type: Optional[str] = None
) -> Dict[str, Any]:
    """
    Uploads a file from ADK artifacts to a Google Cloud Storage bucket.
    
    Args:
        tool_context: The tool context for ADK
        bucket_name: The name of the GCS bucket to upload to
        file_artifact_name: The name of the artifact file in the ADK session
        destination_blob_name: The name to give the file in GCS (defaults to artifact name)
        content_type: The content type of the file (defaults to PDF)
        
    Returns:
        A dictionary containing the upload status and details
    """

    bucket_name = "cymbal-document"
    
    if content_type is None:
        content_type = GCS_DEFAULT_CONTENT_TYPE
    try:
        # Check if user_content contains a PDF attachment
        if (hasattr(tool_context, "user_content") and 
            tool_context.user_content and 
            tool_context.user_content.parts):
            
            # Look for any file in parts
            file_data = None
            for part in tool_context.user_content.parts:
                if hasattr(part, "inline_data") and part.inline_data:
                    if part.inline_data.mime_type.startswith("application/"):
                        file_data = part.inline_data.data
                        break
            
            if file_data:
                # We found file data in the user message
                if not destination_blob_name:
                    destination_blob_name = "DEV/" + file_artifact_name
                    if content_type == "application/pdf" and not destination_blob_name.lower().endswith(".pdf"):
                        destination_blob_name += ".pdf"
                
                # Upload to GCS
                client = storage.Client(project=PROJECT_ID)
                bucket = client.bucket(bucket_name)
                blob = bucket.blob(destination_blob_name)
                
                blob.upload_from_string(
                    data=file_data,
                    content_type=content_type
                )
                
                # Generate a URL
                try:
                    url = blob.public_url
                except:
                    url = f"gs://{bucket_name}/{destination_blob_name}"
                
                return {
                    "status": "success",
                    "bucket": bucket_name,
                    "filename": destination_blob_name,
                    "gcs_uri": f"gs://{bucket_name}/{destination_blob_name}",
                    "size_bytes": len(file_data),
                    "content_type": content_type,
                    "url": url,
                    "message": f"Successfully uploaded file to gs://{bucket_name}/{destination_blob_name}"
                }
        
        # If no file found in user content, return error
        return {
            "status": "error",
            "message": "No file found in the current message. Please upload a file and try again.",
            "details": "Files must be attached directly to the current message."
        }
    except GoogleAPIError as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"Failed to upload file: {str(e)}"
        }
    except Exception as e:
        return {
            "status": "error",
            "error_message": str(e),
            "message": f"An unexpected error occurred: {str(e)}"
        }

# Create FunctionTools from the functions
list_buckets_tool = FunctionTool(list_gcs_buckets)
get_bucket_details_tool = FunctionTool(get_bucket_details)
list_blobs_tool = FunctionTool(list_blobs_in_bucket)
upload_file_gcs_tool = FunctionTool(upload_file_to_gcs) 