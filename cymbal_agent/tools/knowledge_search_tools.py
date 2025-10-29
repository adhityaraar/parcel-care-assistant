"""
Vertex AI Vector Search Tools for ADK

This module ingests and queries enterprise documents using Google Cloud Vertex AI Vector Search,
and is designed to be wrapped as ADK tools/actions.
"""

import os, io, uuid
import json, hashlib
from typing import List, Dict, Tuple
import vertexai

from google.cloud import aiplatform_v1
# from google.genai import Client as GenAIClient
from google import genai
from google.genai.types import EmbedContentConfig
from google.adk.tools import ToolContext, FunctionTool

from dotenv import load_dotenv
load_dotenv()

PROJECT_ID = os.getenv("PROJECT_ID")
LOCATION = os.getenv("LOCATION")
# VERTEX_API_KEY = os.getenv("VERTEX_API_KEY")

VECTOR_DEFAULT_MODEL_NAME = os.getenv("VECTOR_DEFAULT_MODEL_NAME")
VECTOR_DEFAULT_EMBED_DIM = int(os.getenv("VECTOR_DEFAULT_EMBED_DIM"))
VECTOR_DEFAULT_INDEX_ENDPOINT = os.getenv("VECTOR_DEFAULT_INDEX_ENDPOINT")
VECTOR_DEFAULT_DEPLOYED_ID = os.getenv("VECTOR_DEFAULT_DEPLOYED_ID")
VECTOR_DEFAULT_API_ENDPOINT = os.getenv("VECTOR_DEFAULT_API_ENDPOINT")


vertexai.init(project=PROJECT_ID, location=LOCATION)
# genai_client = GenAIClient(api_key=VERTEX_API_KEY)
genai_client = genai.Client(vertexai=True)

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



### ---
from google.cloud import storage
storage_client = storage.Client()

# ========= GCS HELPERS =========
def parse_gcs_uri(uri: str) -> Tuple[str, str]:
    assert uri.startswith("gs://")
    path = uri[len("gs://"):]
    bucket, _, prefix = path.partition("/")
    return bucket, prefix


def list_gcs_files(gcs_prefix: str, exts={".pdf", ".txt"}) -> List[str]:
    bucket_name, prefix = parse_gcs_uri(gcs_prefix)
    bucket = storage_client.bucket(bucket_name)
    blobs = storage_client.list_blobs(bucket, prefix=prefix)
    out = []
    for b in blobs:
        name = b.name.lower()
        if any(name.endswith(ext) for ext in exts):
            out.append(f"gs://{bucket_name}/{b.name}")
    return out

def read_gcs_text(gcs_uri: str) -> str:
    """Read a .txt object from GCS and return utf-8 text"""
    bucket_name, path = parse_gcs_uri(gcs_uri)
    blob = storage_client.bucket(bucket_name).blob(path)
    raw = blob.download_as_bytes()
    return raw.decode("utf-8", errors="ignore")

def read_gcs_pdf_text(gcs_uri: str) -> str:
    """Extract text from PDF in GCS using PyPDF2 (simple); falls back to blank if unreadable."""
    from PyPDF2 import PdfReader
    bucket_name, path = parse_gcs_uri(gcs_uri)
    blob = storage_client.bucket(bucket_name).blob(path)
    pdf_bytes = io.BytesIO(blob.download_as_bytes())
    try:
        reader = PdfReader(pdf_bytes)
        pages = []
        for p in reader.pages:
            try:
                pages.append(p.extract_text() or "")
            except Exception:
                pages.append("")
        return "\n".join(pages)
    except Exception as e:
        print(f"[WARN] PDF extract failed for {gcs_uri}: {e}")
        return ""


# ========= CHUNKING =========
def clean_text(s: str) -> str:
    # normalize whitespace a bit
    return " ".join(s.split())

def chunk_text(text: str, chunk_chars=1000, overlap=100) -> List[str]:
    text = clean_text(text)
    if not text:
        return []
    chunks = []
    i = 0
    n = len(text)
    while i < n:
        end = min(i + chunk_chars, n)
        chunks.append(text[i:end])
        if end == n:
            break
        i = max(end - overlap, i + 1)
    return chunks


def embed_texts(texts: List[str], dim: int = VECTOR_DEFAULT_EMBED_DIM) -> List[List[float]]:
    resp = genai_client.models.embed_content(
        model=VECTOR_DEFAULT_MODEL_NAME,
        contents=texts,
        config=EmbedContentConfig(
            task_type="RETRIEVAL_DOCUMENT",  # good default for RAG docs/queries
            output_dimensionality=dim       # 3072 / 1536 / 768
        ),
    )
    return [e.values for e in resp.embeddings]

# ========= UPSERT =========
def stable_uuid(namespace: uuid.UUID, key: str) -> str:
    """Deterministic ID from path+chunk_index so re-runs don't create duplicates."""
    return str(uuid.uuid5(namespace, key))

def upsert_docs(index_resource_name: str, chunks: List[Tuple[str, str]]):
    """
    chunks: list of (chunk_id, chunk_text)
    """
    if not chunks:
        print("No chunks to upsert.")
        return {}

    ids   = [cid for cid, _ in chunks]
    texts = [txt for _, txt in chunks]

    print(f"Embedding {len(texts)} chunks...")
    vecs = embed_texts(texts)

    print("Creating datapoints...")
    dps = []
    for cid, vec, chunk in zip(ids, vecs, texts):
        # Keep your original idea: put content in restricts (note caveat in the note below)
        restrict = IndexDatapoint.Restriction(namespace="content", allow_list=[chunk])
        dp = IndexDatapoint(datapoint_id=cid, feature_vector=vec, restricts=[restrict])
        dps.append(dp)

    print(f"Upserting {len(dps)} datapoints to Vector Search index: {index_resource_name}")
    idx = MatchingEngineIndex(index_name=index_resource_name)
    # batch to be kind to the service
    BATCH = 100
    for i in range(0, len(dps), BATCH):
        idx.upsert_datapoints(datapoints=dps[i : i + BATCH])
    print("Upsert complete.")

    return {cid: txt for cid, txt in chunks}

# ========= MAPPING PERSISTENCE =========
def load_mapping_from_gcs(mapping_uri: str) -> Dict[str, Dict]:
    try:
        bucket_name, path = parse_gcs_uri(mapping_uri)
        blob = storage_client.bucket(bucket_name).blob(path)
        if not blob.exists():
            return {}
        data = json.loads(blob.download_as_bytes().decode("utf-8"))
        return data
    except Exception as e:
        print(f"[WARN] Could not load mapping from {mapping_uri}: {e}")
        return {}

def save_mapping_to_gcs(mapping_uri: str, mapping: Dict[str, Dict]):
    bucket_name, path = parse_gcs_uri(mapping_uri)
    blob = storage_client.bucket(bucket_name).blob(path)
    blob.upload_from_string(json.dumps(mapping, ensure_ascii=False, indent=2), content_type="application/json")
    print(f"Saved mapping to {mapping_uri}")


# ========= MAIN PIPELINE =========
def build_and_upsert(gcs_prefix: str, index_resource_name: str, mapping_uri: str):
    # Collect files
    files = list_gcs_files(gcs_prefix, exts={".pdf", ".txt"})
    if not files:
        print(f"No .pdf or .txt files found in {gcs_prefix}")
        return

    print(f"Found {len(files)} files under {gcs_prefix}")

    # Load existing mapping (merge later)
    existing = load_mapping_from_gcs(mapping_uri)
    mapping  = dict(existing)  # id -> {src, i, text}

    # Deterministic namespace for IDs (per bucket/prefix)
    ns_seed = hashlib.sha256(gcs_prefix.encode("utf-8")).hexdigest()
    ns = uuid.UUID(ns_seed[0:32])

    # Gather chunks (id, text) and a sidecar for provenance
    to_upsert: List[Tuple[str, str]] = []
    provenance: Dict[str, Dict] = {}  # id -> {src, i}

    for f in files:
        print(f"Reading {f} ...")
        if f.lower().endswith(".txt"):
            text = read_gcs_text(f)
        else:
            text = read_gcs_pdf_text(f)

        chunks = chunk_text(text, chunk_chars=1000, overlap=100)
        if not chunks:
            print(f"[WARN] No text extracted from {f}")
            continue

        for i, ch in enumerate(chunks):
            cid = stable_uuid(ns, f"{f}::chunk::{i}")
            to_upsert.append((cid, ch))
            provenance[cid] = {"src": f, "i": i}

    if not to_upsert:
        print("Nothing to upsert after extraction.")
        return

    # Upsert
    id2text = upsert_docs(index_resource_name, to_upsert)

    # Merge into mapping and save (locally + GCS)
    for cid, meta in provenance.items():
        mapping[cid] = {
            "source": meta["src"],
            "chunk_index": meta["i"],
            "text": id2text.get(cid, "")
        }

    # Also keep a local backup
    with open("vector_mapping.json", "w", encoding="utf-8") as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)
    print("Saved local vector_mapping.json")

    # Push to GCS
    save_mapping_to_gcs(mapping_uri, mapping)

    print(f"All done. Upserted {len(to_upsert)} chunks from {len(files)} files.")


# Create FunctionTools from the functions
query_documents_tool = FunctionTool(retrieve_documents)
build_and_upsert_tool = FunctionTool(build_and_upsert)