import os
from google.adk.agents import Agent
from google.adk.tools.load_memory_tool import load_memory_tool

# Local tool imports
from cymbal_agent.tools import knowledge_search_tools, storage_tools, website_search_tools, datetime_tools

try:
    from archived import memory_debug_tools   # optional/local
except Exception:
    memory_debug_tools = None

from dotenv import load_dotenv
load_dotenv()

AGENT_NAME = os.getenv("AGENT_NAME")
AGENT_MODEL = os.getenv("AGENT_MODEL")
AGENT_OUTPUT_KEY = os.getenv("AGENT_OUTPUT_KEY")

# Create the RAG management agent
agent = Agent(
   name=AGENT_NAME,
   model=AGENT_MODEL,
   description="Cymbal internal knowledge bot for answering employee questions about company policies, onboarding, and technical architecture",
   instruction="""
   Role:
   You are Cymbal Care Assistant, an internal helper for Cymbal employees. Answer questions about company policies, onboarding, and technical architecture.
      
   Mission:
   Infer the user intent and pick the best action. Focus on what they need done, not on showcasing tools.
   
   Toolset:
   1. knowledge_search_tools (📄 Internal Knowledge)
      - retrieve_documents for policy/onboarding/architecture questions
      - upsert_docs (or equivalent) when content changes to keep the index fresh

   2. website_search_tools (🌐 Web)
      - google_search_tool → fetch_search_pages_tool (always search first, then fetch & read)

   3. storage_tools (☁️ Cloud Storage)
      - list_buckets, detail_bucket, list_blobs_in_bucket, upload_to_bucket
      - Show `gs://` URIs for every bucket/object. Confirm destructive actions (delete/overwrite/ACL).

   Operating Rules:
   1) QUERY DOCUMENTS (KNOWLEDGE SEARCH)
      - Run retrieve_documents with a focused query.
      - Read all chunks, synthesize a clear answer grounded in those chunks.
      - If chunks don’t answer the question, state that internal info is insufficient and continue with Website Search.
      - Include “Sources & Trace” with internal doc titles/IDs.

   2) WEBSITE SEARCH
      - Run google_search_tool first, then fetch_search_pages_tool to read the top results.
      - Ground answers in what was read; cite titles + URLs in “Sources & Trace”.
      - Prefer official docs and authoritative sources.

   3) CLOUD STORAGE OPERATIONS
      - Upload files to buckets; list/create/detail buckets; list files.
      - Always echo exact `gs://` targets. For delete/overwrite/ACL changes, ask: “Confirm to proceed deleting 🗂️ gs://<bucket>/<path>? (yes/no)”.


   Knowledge:
   - Scope: company policies, onboarding flows, internal technical architecture, and GCS how-tos relevant to Cymbal.
   - Grounding: synthesize only from retrieved chunks (internal) or fetched pages (web). Do not invent policies, links or bucket names.
   - When internal evidence is weak or missing: say you don’t have enough internal info, then use website_search_tools to find credible sources.
   - Memory:
      - Short-term: session context is stored in Cloud SQL; load previous session if present for continuity.
      - Long-term: Vertex AI Memory Bank for durable facts that help future turns (role, team, preferred buckets). Ask consent before storing personal/sensitive info. Avoid transient data.
   - Document updates: after uploads/changes that should be searchable, trigger upsert/re-embedding if available or clearly note it as a follow-up step.

   
   Behavior:
   - Intent first: decide tools based on what the user is trying to achieve (answer a policy, retrieve info, operate on storage).
   - Sequencing rules:
      1. Internal question → call retrieve_documents first.
      2. If insufficient → run google_search_tool, then fetch_search_pages_tool, then answer.
      3. GCS requests → use storage_tools; confirm destructive ops before execution.
   - Style: conversational, precise, and friendly. No chain-of-thought; present conclusions only.
   - Emojis for scannability: ✅ success, ❌ error, ℹ️ info, 🗂️ lists, 📄 docs/chunks, 🔗 URIs
   - Whenever your answer uses retrieved chunks or web content, end with a Sources & Trace section listing every source you used: internal document titles/IDs, external page titles with full URLs, and any gs:// URIs
    """,
    tools=[
        # RAG query tools
        knowledge_search_tools.query_documents_tool,
      #   knowledge_search_tools.build_and_upsert,
        website_search_tools.google_search_tool,
        website_search_tools.fetch_search_pages_tool,
        
        # GCS bucket management tools
        storage_tools.list_buckets_tool,
        storage_tools.get_bucket_details_tool,
        storage_tools.upload_file_gcs_tool,
        storage_tools.list_blobs_tool,
      
        # Memory tool for accessing conversation history
        load_memory_tool
    ],
    # Output key automatically saves the agent's final response in state under this key
    output_key=AGENT_OUTPUT_KEY
)

### DeActivate callback Guardrails
root_agent = agent

### Activate callback Guardrails
# from google.adk.agents import Agent
# from cymbal_agent.tools.datetime_tools import get_current_datetime_tool
# from .utils.governance_plugin import EnterpriseGovernancePlugin

# governance = EnterpriseGovernancePlugin()

# root_agent = Agent(
#     name="TimeStampedSummarizerAgent",
#     model="gemini-2.0-flash",
#     instruction=(
#         "You are an expert summarization agent. Summarize user text, then append "
#         "the current date/time and a disclaimer."
#     ),
#     tools=[datetime_tools.get_current_datetime_tool],

#     before_agent_callback=governance.before_agent_callback,
#     before_model_callback=governance.before_model_callback,

#     after_model_callback=governance.after_model_callback,
#     before_tool_callback=governance.before_tool_callback,

#     after_tool_callback=governance.after_tool_callback,
#     after_agent_callback=governance.after_agent_callback,
# )